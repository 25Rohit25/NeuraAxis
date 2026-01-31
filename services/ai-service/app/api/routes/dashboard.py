"""
NEURAXIS - Case Dashboard API
Optimized endpoints for case dashboard with faceted search
"""

import csv
from datetime import datetime, timedelta
from io import StringIO
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, asc, desc, func, or_, select
from sqlalchemy import case as sql_case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.case import CaseStatus, MedicalCase, UrgencyLevel
from app.models.patient import Patient
from app.models.user import User

router = APIRouter(prefix="/cases", tags=["case-dashboard"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class PatientSummary(BaseModel):
    id: str
    mrn: str
    full_name: str
    age: int
    gender: str
    avatar_url: Optional[str] = None


class DoctorSummary(BaseModel):
    id: str
    name: str
    specialty: str
    avatar_url: Optional[str] = None


class LastActivity(BaseModel):
    action: str
    by: str
    at: str


class CaseSummaryResponse(BaseModel):
    id: str
    case_number: str
    patient: PatientSummary
    chief_complaint: str
    primary_diagnosis: Optional[str] = None
    priority: str
    status: str
    assigned_to: DoctorSummary
    created_by: DoctorSummary
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    symptoms_count: int
    images_count: int
    has_ai_suggestions: bool
    is_unread: Optional[bool] = None
    last_activity: Optional[LastActivity] = None


class DashboardStats(BaseModel):
    active_count: int
    urgent_count: int
    pending_review_count: int
    completed_today: int
    avg_resolution_time: float
    total_this_week: int


class PriorityFacet(BaseModel):
    value: str
    count: int


class StatusFacet(BaseModel):
    value: str
    count: int


class DoctorFacet(BaseModel):
    id: str
    name: str
    count: int


class FilterFacets(BaseModel):
    priorities: List[PriorityFacet]
    statuses: List[StatusFacet]
    doctors: List[DoctorFacet]


class DashboardResponse(BaseModel):
    cases: List[CaseSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    stats: Optional[DashboardStats] = None
    facets: Optional[FilterFacets] = None


class BulkActionRequest(BaseModel):
    case_ids: List[str]
    action: str
    target_doctor_id: Optional[str] = None
    target_priority: Optional[str] = None
    target_status: Optional[str] = None


class AssignRequest(BaseModel):
    doctor_id: str


class StatusUpdateRequest(BaseModel):
    status: str


# =============================================================================
# Helper Functions
# =============================================================================


def calculate_age(dob: datetime) -> int:
    """Calculate age from date of birth."""
    today = datetime.now()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def case_to_summary(case: MedicalCase) -> CaseSummaryResponse:
    """Convert MedicalCase to CaseSummaryResponse."""
    patient = case.patient
    assigned = case.assigned_doctor
    creator = case.created_by_doctor

    return CaseSummaryResponse(
        id=str(case.id),
        case_number=case.case_number,
        patient=PatientSummary(
            id=str(patient.id),
            mrn=patient.mrn,
            full_name=f"{patient.first_name} {patient.last_name}",
            age=calculate_age(patient.date_of_birth),
            gender=patient.gender,
            avatar_url=getattr(patient, "avatar_url", None),
        ),
        chief_complaint=case.chief_complaint or "",
        primary_diagnosis=case.primary_diagnosis,
        priority=case.urgency_level.value if case.urgency_level else "moderate",
        status=case.status.value if case.status else "pending",
        assigned_to=DoctorSummary(
            id=str(assigned.id),
            name=f"{assigned.first_name} {assigned.last_name}",
            specialty=getattr(assigned, "specialty", "General"),
            avatar_url=getattr(assigned, "avatar_url", None),
        )
        if assigned
        else DoctorSummary(id="", name="Unassigned", specialty=""),
        created_by=DoctorSummary(
            id=str(creator.id),
            name=f"{creator.first_name} {creator.last_name}",
            specialty=getattr(creator, "specialty", "General"),
            avatar_url=getattr(creator, "avatar_url", None),
        )
        if creator
        else DoctorSummary(id="", name="System", specialty=""),
        created_at=case.created_at.isoformat(),
        updated_at=case.updated_at.isoformat(),
        completed_at=case.completed_at.isoformat() if case.completed_at else None,
        symptoms_count=len(case.symptoms) if case.symptoms else 0,
        images_count=len(case.images) if case.images else 0,
        has_ai_suggestions=bool(case.ai_suggestions),
        is_unread=False,  # Would check user's read status
        last_activity=None,
    )


async def get_dashboard_stats(db: AsyncSession, user_id: UUID) -> DashboardStats:
    """Calculate dashboard statistics."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)

    # Active cases count
    active_result = await db.execute(
        select(func.count(MedicalCase.id)).where(
            MedicalCase.assigned_doctor_id == user_id,
            MedicalCase.status.in_([CaseStatus.pending, CaseStatus.in_progress]),
        )
    )
    active_count = active_result.scalar() or 0

    # Urgent cases count
    urgent_result = await db.execute(
        select(func.count(MedicalCase.id)).where(
            MedicalCase.urgency_level.in_([UrgencyLevel.high, UrgencyLevel.critical]),
            MedicalCase.status.in_([CaseStatus.pending, CaseStatus.in_progress]),
        )
    )
    urgent_count = urgent_result.scalar() or 0

    # Pending review
    pending_result = await db.execute(
        select(func.count(MedicalCase.id)).where(MedicalCase.status == CaseStatus.pending)
    )
    pending_review_count = pending_result.scalar() or 0

    # Completed today
    completed_result = await db.execute(
        select(func.count(MedicalCase.id)).where(
            MedicalCase.status == CaseStatus.completed, MedicalCase.completed_at >= today
        )
    )
    completed_today = completed_result.scalar() or 0

    # Average resolution time (hours)
    avg_time_result = await db.execute(
        select(
            func.avg(
                func.extract("epoch", MedicalCase.completed_at - MedicalCase.created_at) / 3600
            )
        ).where(MedicalCase.status == CaseStatus.completed, MedicalCase.completed_at.isnot(None))
    )
    avg_resolution_time = avg_time_result.scalar() or 0

    # Total this week
    week_result = await db.execute(
        select(func.count(MedicalCase.id)).where(MedicalCase.created_at >= week_ago)
    )
    total_this_week = week_result.scalar() or 0

    return DashboardStats(
        active_count=active_count,
        urgent_count=urgent_count,
        pending_review_count=pending_review_count,
        completed_today=completed_today,
        avg_resolution_time=round(avg_resolution_time, 1) if avg_resolution_time else 0,
        total_this_week=total_this_week,
    )


async def get_filter_facets(db: AsyncSession, base_query) -> FilterFacets:
    """Calculate filter facets for the current query."""
    # Priority facets
    priority_result = await db.execute(
        select(MedicalCase.urgency_level, func.count(MedicalCase.id)).group_by(
            MedicalCase.urgency_level
        )
    )
    priorities = [
        PriorityFacet(value=row[0].value if row[0] else "moderate", count=row[1])
        for row in priority_result.fetchall()
    ]

    # Status facets
    status_result = await db.execute(
        select(MedicalCase.status, func.count(MedicalCase.id)).group_by(MedicalCase.status)
    )
    statuses = [
        StatusFacet(value=row[0].value if row[0] else "pending", count=row[1])
        for row in status_result.fetchall()
    ]

    # Doctor facets
    doctor_result = await db.execute(
        select(User.id, User.first_name, User.last_name, func.count(MedicalCase.id))
        .join(MedicalCase, MedicalCase.assigned_doctor_id == User.id)
        .group_by(User.id, User.first_name, User.last_name)
        .order_by(desc(func.count(MedicalCase.id)))
        .limit(10)
    )
    doctors = [
        DoctorFacet(id=str(row[0]), name=f"{row[1]} {row[2]}", count=row[3])
        for row in doctor_result.fetchall()
    ]

    return FilterFacets(
        priorities=priorities,
        statuses=statuses,
        doctors=doctors,
    )


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_cases(
    view: str = Query("active"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_field: str = Query("updatedAt"),
    sort_direction: str = Query("desc"),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    # current_user would come from auth dependency
):
    """Get paginated cases for dashboard with filters and facets."""

    # TODO: Get current user from auth
    current_user_id = UUID("00000000-0000-0000-0000-000000000001")

    # Base query with eager loading
    query = select(MedicalCase).options(
        selectinload(MedicalCase.patient),
        selectinload(MedicalCase.assigned_doctor),
        selectinload(MedicalCase.created_by_doctor),
        selectinload(MedicalCase.symptoms),
        selectinload(MedicalCase.images),
    )

    # View-based filters
    if view == "active":
        query = query.where(
            MedicalCase.assigned_doctor_id == current_user_id,
            MedicalCase.status.in_([CaseStatus.pending, CaseStatus.in_progress]),
        )
    elif view == "urgent":
        query = query.where(
            MedicalCase.urgency_level.in_([UrgencyLevel.high, UrgencyLevel.critical]),
            MedicalCase.status.in_([CaseStatus.pending, CaseStatus.in_progress]),
        )
    elif view == "pending":
        query = query.where(MedicalCase.status == CaseStatus.pending)
    elif view == "closed":
        query = query.where(MedicalCase.status == CaseStatus.completed)
    elif view == "team":
        # Cases from team members (would need team logic)
        query = query.where(MedicalCase.status != CaseStatus.archived)

    # Priority filter
    if priority:
        priorities = [p.strip() for p in priority.split(",")]
        priority_enums = [
            UrgencyLevel(p) for p in priorities if p in [e.value for e in UrgencyLevel]
        ]
        if priority_enums:
            query = query.where(MedicalCase.urgency_level.in_(priority_enums))

    # Status filter
    if status:
        statuses = [s.strip() for s in status.split(",")]
        status_enums = [CaseStatus(s) for s in statuses if s in [e.value for e in CaseStatus]]
        if status_enums:
            query = query.where(MedicalCase.status.in_(status_enums))

    # Assigned doctor filter
    if assigned_to:
        doctor_ids = [UUID(d.strip()) for d in assigned_to.split(",")]
        query = query.where(MedicalCase.assigned_doctor_id.in_(doctor_ids))

    # Date range filter
    if date_start:
        query = query.where(MedicalCase.created_at >= datetime.fromisoformat(date_start))
    if date_end:
        query = query.where(MedicalCase.created_at <= datetime.fromisoformat(date_end))

    # Search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.join(Patient).where(
            or_(
                MedicalCase.case_number.ilike(search_pattern),
                MedicalCase.chief_complaint.ilike(search_pattern),
                MedicalCase.primary_diagnosis.ilike(search_pattern),
                Patient.first_name.ilike(search_pattern),
                Patient.last_name.ilike(search_pattern),
                Patient.mrn.ilike(search_pattern),
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sorting
    sort_map = {
        "createdAt": MedicalCase.created_at,
        "updatedAt": MedicalCase.updated_at,
        "priority": MedicalCase.urgency_level,
        "patientName": Patient.last_name,
    }
    sort_column = sort_map.get(sort_field, MedicalCase.updated_at)
    if sort_direction == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    cases = result.scalars().all()

    # Convert to response
    case_summaries = [case_to_summary(c) for c in cases]

    # Get stats and facets (only on first page for performance)
    stats = None
    facets = None
    if page == 1:
        stats = await get_dashboard_stats(db, current_user_id)
        facets = await get_filter_facets(db, query)

    total_pages = (total + page_size - 1) // page_size

    return DashboardResponse(
        cases=case_summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        stats=stats,
        facets=facets,
    )


@router.post("/bulk")
async def execute_bulk_action(
    request: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute bulk action on multiple cases."""

    case_ids = [UUID(cid) for cid in request.case_ids]

    if request.action == "assign" and request.target_doctor_id:
        doctor_id = UUID(request.target_doctor_id)
        await db.execute(
            MedicalCase.__table__.update()
            .where(MedicalCase.id.in_(case_ids))
            .values(assigned_doctor_id=doctor_id, updated_at=datetime.now())
        )

    elif request.action == "change_priority" and request.target_priority:
        await db.execute(
            MedicalCase.__table__.update()
            .where(MedicalCase.id.in_(case_ids))
            .values(urgency_level=UrgencyLevel(request.target_priority), updated_at=datetime.now())
        )

    elif request.action == "change_status" and request.target_status:
        values = {"status": CaseStatus(request.target_status), "updated_at": datetime.now()}
        if request.target_status == "completed":
            values["completed_at"] = datetime.now()

        await db.execute(
            MedicalCase.__table__.update().where(MedicalCase.id.in_(case_ids)).values(**values)
        )

    elif request.action == "archive":
        await db.execute(
            MedicalCase.__table__.update()
            .where(MedicalCase.id.in_(case_ids))
            .values(status=CaseStatus.archived, updated_at=datetime.now())
        )

    elif request.action == "delete":
        # Soft delete
        await db.execute(
            MedicalCase.__table__.update()
            .where(MedicalCase.id.in_(case_ids))
            .values(is_deleted=True, updated_at=datetime.now())
        )

    await db.commit()

    return {"success": True, "affected": len(case_ids)}


@router.post("/{case_id}/assign")
async def assign_case(
    case_id: UUID,
    request: AssignRequest,
    db: AsyncSession = Depends(get_db),
):
    """Assign a case to a doctor."""

    result = await db.execute(select(MedicalCase).where(MedicalCase.id == case_id))
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.assigned_doctor_id = UUID(request.doctor_id)
    case.updated_at = datetime.now()

    await db.commit()

    # TODO: Send notification to new assignee
    # TODO: Broadcast WebSocket event

    return {"success": True}


@router.patch("/{case_id}/status")
async def update_case_status(
    case_id: UUID,
    request: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update case status."""

    result = await db.execute(select(MedicalCase).where(MedicalCase.id == case_id))
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = CaseStatus(request.status)
    case.updated_at = datetime.now()

    if request.status == "completed":
        case.completed_at = datetime.now()

    await db.commit()

    return {"success": True}


@router.post("/{case_id}/archive")
async def archive_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Archive a case."""

    result = await db.execute(select(MedicalCase).where(MedicalCase.id == case_id))
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = CaseStatus.archived
    case.updated_at = datetime.now()

    await db.commit()

    return {"success": True}


@router.get("/export")
async def export_cases(
    ids: Optional[str] = Query(None),
    view: str = Query("active"),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Export cases to CSV."""

    # Build query
    query = select(MedicalCase).options(
        selectinload(MedicalCase.patient),
        selectinload(MedicalCase.assigned_doctor),
    )

    if ids:
        case_ids = [UUID(cid.strip()) for cid in ids.split(",")]
        query = query.where(MedicalCase.id.in_(case_ids))
    else:
        # Apply view filter
        if view == "active":
            query = query.where(
                MedicalCase.status.in_([CaseStatus.pending, CaseStatus.in_progress])
            )
        elif view == "urgent":
            query = query.where(
                MedicalCase.urgency_level.in_([UrgencyLevel.high, UrgencyLevel.critical])
            )

        if search:
            search_pattern = f"%{search}%"
            query = query.join(Patient).where(
                or_(
                    MedicalCase.case_number.ilike(search_pattern),
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                )
            )

    result = await db.execute(query)
    cases = result.scalars().all()

    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "Case Number",
            "Patient Name",
            "MRN",
            "Chief Complaint",
            "Primary Diagnosis",
            "Priority",
            "Status",
            "Assigned To",
            "Created At",
            "Updated At",
        ]
    )

    # Data rows
    for case in cases:
        patient = case.patient
        doctor = case.assigned_doctor

        writer.writerow(
            [
                case.case_number,
                f"{patient.first_name} {patient.last_name}" if patient else "",
                patient.mrn if patient else "",
                case.chief_complaint or "",
                case.primary_diagnosis or "",
                case.urgency_level.value if case.urgency_level else "",
                case.status.value if case.status else "",
                f"{doctor.first_name} {doctor.last_name}" if doctor else "",
                case.created_at.isoformat() if case.created_at else "",
                case.updated_at.isoformat() if case.updated_at else "",
            ]
        )

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=cases-export-{datetime.now().strftime('%Y-%m-%d')}.csv"
        },
    )
