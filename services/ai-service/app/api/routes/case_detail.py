"""
NEURAXIS - Case Detail API Endpoints
Comprehensive endpoints for case detail view with collaboration
"""

import json
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.case import (
    CaseAuditLog,
    CaseComment,
    CaseImage,
    CaseLock,
    CaseMedication,
    CaseNote,
    CaseStatus,
    CaseSymptom,
    CaseTreatmentPlan,
    CaseVersion,
    MedicalCase,
    UrgencyLevel,
)
from app.models.patient import Patient
from app.models.user import User
from app.services.audit_logger import log_case_action
from app.services.pdf_export import generate_case_pdf

router = APIRouter(prefix="/cases", tags=["case-detail"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class UpdateSectionRequest(BaseModel):
    section: str
    data: dict
    version: int


class AddCommentRequest(BaseModel):
    section_id: str
    section_type: str
    content: str
    mentions: list[str] | None = None
    parent_id: str | None = None


class ExportOptions(BaseModel):
    format: str = "pdf"
    sections: list[str] = ["all"]
    include_images: bool = True
    include_ai_analysis: bool = True
    include_comments: bool = False
    is_print_optimized: bool = False


class LockRequest(BaseModel):
    section: str | None = None


class AuditLogEntry(BaseModel):
    id: str
    action: str
    section: str
    actor_id: str
    actor_name: str
    timestamp: str
    details: dict | None = None


# =============================================================================
# Case Detail Endpoints
# =============================================================================


@router.get("/{case_id}")
async def get_case_detail(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full case detail with all related data."""

    query = (
        select(MedicalCase)
        .options(
            selectinload(MedicalCase.patient),
            selectinload(MedicalCase.assigned_doctor),
            selectinload(MedicalCase.created_by_doctor),
            selectinload(MedicalCase.symptoms),
            selectinload(MedicalCase.medications),
            selectinload(MedicalCase.images),
            selectinload(MedicalCase.notes),
            selectinload(MedicalCase.treatment_plan),
            selectinload(MedicalCase.comments).selectinload(CaseComment.author),
            selectinload(MedicalCase.care_team),
        )
        .where(MedicalCase.id == case_id)
    )

    result = await db.execute(query)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Check access control
    if not can_access_case(current_user, case):
        raise HTTPException(status_code=403, detail="Access denied")

    # Log access
    await log_case_action(db, case_id, current_user.id, "viewed", details={"section": "full"})

    # Check lock status
    lock = await get_case_lock(db, case_id)

    return {
        **case_to_detail(case),
        "isLocked": lock is not None,
        "lockedBy": {"fullName": lock.user.first_name + " " + lock.user.last_name}
        if lock
        else None,
        "version": case.version,
    }


@router.patch("/{case_id}")
async def update_case_section(
    case_id: UUID,
    request: UpdateSectionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific section of the case with optimistic locking."""

    # Get case with lock check
    query = select(MedicalCase).where(MedicalCase.id == case_id)
    result = await db.execute(query)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Check access
    if not can_edit_case(current_user, case):
        raise HTTPException(status_code=403, detail="Edit access denied")

    # Optimistic locking check
    if case.version != request.version:
        raise HTTPException(
            status_code=409, detail="Case was modified by another user. Please refresh."
        )

    # Create version snapshot before update
    await create_version_snapshot(db, case, request.section, current_user.id)

    # Apply update based on section
    old_data = get_section_data(case, request.section)
    await apply_section_update(db, case, request.section, request.data)

    # Increment version
    case.version += 1
    case.updated_at = datetime.now()
    case.last_edited_by_id = current_user.id

    await db.commit()
    await db.refresh(case)

    # Log audit
    background_tasks.add_task(
        log_case_action,
        db,
        case_id,
        current_user.id,
        "updated",
        details={"section": request.section, "old": old_data, "new": request.data},
    )

    # Broadcast update via WebSocket (background task)
    background_tasks.add_task(broadcast_case_update, case_id, request.section, current_user.id)

    return case_to_detail(case)


# =============================================================================
# Timeline Endpoints
# =============================================================================


@router.get("/{case_id}/timeline")
async def get_case_timeline(
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get paginated timeline events for a case."""

    query = (
        select(CaseAuditLog)
        .where(CaseAuditLog.case_id == case_id)
        .order_by(desc(CaseAuditLog.timestamp))
        .offset((page - 1) * page_size)
        .limit(page_size + 1)
    )

    result = await db.execute(query)
    events = result.scalars().all()

    has_more = len(events) > page_size
    events = events[:page_size]

    return {
        "events": [audit_to_timeline_event(e) for e in events],
        "page": page,
        "hasMore": has_more,
    }


# =============================================================================
# Comments Endpoints
# =============================================================================


@router.get("/{case_id}/comments")
async def get_case_comments(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all comment threads for a case."""

    query = (
        select(CaseComment)
        .options(
            selectinload(CaseComment.author),
            selectinload(CaseComment.replies).selectinload(CaseComment.author),
        )
        .where(
            CaseComment.case_id == case_id,
            CaseComment.parent_id.is_(None),  # Top-level comments only
        )
        .order_by(desc(CaseComment.created_at))
    )

    result = await db.execute(query)
    comments = result.scalars().all()

    return {"threads": [comment_to_thread(c) for c in comments]}


@router.post("/{case_id}/comments")
async def add_comment(
    case_id: UUID,
    request: AddCommentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a comment to a case section."""

    comment = CaseComment(
        id=uuid4(),
        case_id=case_id,
        section_id=request.section_id,
        section_type=request.section_type,
        content=request.content,
        author_id=current_user.id,
        parent_id=UUID(request.parent_id) if request.parent_id else None,
        mentions=request.mentions or [],
        created_at=datetime.now(),
    )

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    # Notify mentioned users
    if request.mentions:
        background_tasks.add_task(
            notify_mentioned_users, case_id, comment.id, request.mentions, current_user.id
        )

    # Log audit
    background_tasks.add_task(
        log_case_action,
        db,
        case_id,
        current_user.id,
        "comment_added",
        details={"section": request.section_id},
    )

    return {
        "id": str(comment.id),
        "threadId": str(comment.parent_id or comment.id),
        "content": comment.content,
        "author": {
            "id": str(current_user.id),
            "lastName": current_user.last_name,
            "fullName": f"{current_user.first_name} {current_user.last_name}",
        },
        "createdAt": comment.created_at.isoformat(),
    }


@router.post("/{case_id}/comments/{thread_id}/resolve")
async def resolve_comment_thread(
    case_id: UUID,
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve a comment thread."""

    result = await db.execute(select(CaseComment).where(CaseComment.id == thread_id))
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Thread not found")

    comment.is_resolved = True
    comment.resolved_at = datetime.now()
    comment.resolved_by_id = current_user.id

    await db.commit()

    return {"success": True}


# =============================================================================
# Version History Endpoints
# =============================================================================


@router.get("/{case_id}/versions")
async def get_version_history(
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get version history for a case."""

    query = (
        select(CaseVersion)
        .options(selectinload(CaseVersion.author))
        .where(CaseVersion.case_id == case_id)
        .order_by(desc(CaseVersion.version))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    versions = result.scalars().all()

    return {
        "versions": [version_to_response(v) for v in versions],
        "page": page,
    }


@router.post("/{case_id}/versions/{version_id}/revert")
async def revert_to_version(
    case_id: UUID,
    version_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revert case to a specific version."""

    # Get version snapshot
    result = await db.execute(select(CaseVersion).where(CaseVersion.id == version_id))
    version = result.scalar_one_or_none()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Get current case
    result = await db.execute(select(MedicalCase).where(MedicalCase.id == case_id))
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Create snapshot of current state before revert
    await create_version_snapshot(db, case, "revert", current_user.id)

    # Apply snapshot data
    if version.snapshot_data:
        await apply_snapshot(db, case, version.snapshot_data)

    case.version += 1
    case.updated_at = datetime.now()

    await db.commit()

    # Log audit
    background_tasks.add_task(
        log_case_action,
        db,
        case_id,
        current_user.id,
        "reverted",
        details={"to_version": version.version},
    )

    return {"success": True, "version": case.version}


@router.get("/{case_id}/versions/compare")
async def compare_versions(
    case_id: UUID,
    v1: UUID,
    v2: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare two versions of a case."""

    result = await db.execute(select(CaseVersion).where(CaseVersion.id.in_([v1, v2])))
    versions = result.scalars().all()

    if len(versions) != 2:
        raise HTTPException(status_code=404, detail="Versions not found")

    v1_data = versions[0].snapshot_data or {}
    v2_data = versions[1].snapshot_data or {}

    # Compute diff
    diff = compute_diff(v1_data, v2_data)

    return {
        "v1": versions[0].version,
        "v2": versions[1].version,
        "diff": diff,
    }


# =============================================================================
# Lock Management Endpoints
# =============================================================================


@router.post("/{case_id}/lock")
async def acquire_case_lock(
    case_id: UUID,
    request: LockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acquire an edit lock on a case or section."""

    # Check for existing lock
    existing = await get_case_lock(db, case_id, request.section)

    if existing and existing.user_id != current_user.id:
        # Check if lock is expired (5 minutes)
        if (datetime.now() - existing.acquired_at).seconds < 300:
            raise HTTPException(
                status_code=423,
                detail="Case is locked",
                headers={"X-Locked-By": f"{existing.user.first_name} {existing.user.last_name}"},
            )
        else:
            # Release expired lock
            await db.delete(existing)

    # Create or update lock
    lock = CaseLock(
        id=uuid4(),
        case_id=case_id,
        user_id=current_user.id,
        section=request.section,
        acquired_at=datetime.now(),
    )

    db.add(lock)
    await db.commit()

    return {"success": True, "lockId": str(lock.id)}


@router.delete("/{case_id}/lock")
async def release_case_lock(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Release an edit lock on a case."""

    result = await db.execute(
        select(CaseLock).where(
            CaseLock.case_id == case_id,
            CaseLock.user_id == current_user.id,
        )
    )
    lock = result.scalar_one_or_none()

    if lock:
        await db.delete(lock)
        await db.commit()

    return {"success": True}


# =============================================================================
# Export Endpoints
# =============================================================================


@router.post("/{case_id}/export")
async def export_case(
    case_id: UUID,
    options: ExportOptions,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export case to PDF/DOCX/HTML."""

    # Get full case data
    query = (
        select(MedicalCase)
        .options(
            selectinload(MedicalCase.patient),
            selectinload(MedicalCase.assigned_doctor),
            selectinload(MedicalCase.symptoms),
            selectinload(MedicalCase.medications),
            selectinload(MedicalCase.images),
            selectinload(MedicalCase.notes),
            selectinload(MedicalCase.treatment_plan),
        )
        .where(MedicalCase.id == case_id)
    )

    result = await db.execute(query)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Generate export
    if options.format == "pdf":
        content = await generate_case_pdf(case, options)
        media_type = "application/pdf"
        filename = f"case-{case.case_number}.pdf"
    elif options.format == "docx":
        content = await generate_case_docx(case, options)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"case-{case.case_number}.docx"
    else:
        content = await generate_case_html(case, options)
        media_type = "text/html"
        filename = f"case-{case.case_number}.html"

    # Log export
    background_tasks.add_task(
        log_case_action,
        db,
        case_id,
        current_user.id,
        "exported",
        details={"format": options.format},
    )

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# =============================================================================
# Audit Log Endpoints
# =============================================================================


@router.get("/{case_id}/audit")
async def get_audit_log(
    case_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get audit log for a case."""

    # Check if user has audit access
    if not current_user.can_view_audit:
        raise HTTPException(status_code=403, detail="Audit access denied")

    query = (
        select(CaseAuditLog)
        .options(selectinload(CaseAuditLog.actor))
        .where(CaseAuditLog.case_id == case_id)
        .order_by(desc(CaseAuditLog.timestamp))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            AuditLogEntry(
                id=str(log.id),
                action=log.action,
                section=log.section or "case",
                actor_id=str(log.actor_id),
                actor_name=f"{log.actor.first_name} {log.actor.last_name}",
                timestamp=log.timestamp.isoformat(),
                details=log.details,
            )
            for log in logs
        ],
        "page": page,
    }


# =============================================================================
# Helper Functions
# =============================================================================


def can_access_case(user: User, case: MedicalCase) -> bool:
    """Check if user can access this case."""
    if user.role == "admin":
        return True
    if case.assigned_doctor_id == user.id:
        return True
    if case.created_by_id == user.id:
        return True
    # Check care team
    if user.id in [m.id for m in (case.care_team or [])]:
        return True
    return False


def can_edit_case(user: User, case: MedicalCase) -> bool:
    """Check if user can edit this case."""
    if case.status in [CaseStatus.completed, CaseStatus.archived]:
        return user.role == "admin"
    return can_access_case(user, case)


async def get_case_lock(
    db: AsyncSession, case_id: UUID, section: str | None = None
) -> CaseLock | None:
    """Get active lock for a case."""
    query = select(CaseLock).options(selectinload(CaseLock.user)).where(CaseLock.case_id == case_id)

    if section:
        query = query.where(CaseLock.section == section)

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_version_snapshot(db: AsyncSession, case: MedicalCase, section: str, user_id: UUID):
    """Create a version snapshot before update."""
    version = CaseVersion(
        id=uuid4(),
        case_id=case.id,
        version=case.version,
        section=section,
        author_id=user_id,
        timestamp=datetime.now(),
        snapshot_data=get_section_data(case, section),
    )
    db.add(version)


def get_section_data(case: MedicalCase, section: str) -> dict:
    """Get current data for a section."""
    section_map = {
        "chiefComplaint": case.chief_complaint,
        "vitals": case.vitals,
        "symptoms": [s.__dict__ for s in (case.symptoms or [])],
        "medications": [m.__dict__ for m in (case.medications or [])],
        "images": [i.__dict__ for i in (case.images or [])],
        "clinicalNotes": [n.__dict__ for n in (case.notes or [])],
        "treatmentPlan": case.treatment_plan.__dict__ if case.treatment_plan else None,
        "aiAnalysis": case.ai_analysis,
    }
    return section_map.get(section, {})


async def apply_section_update(db: AsyncSession, case: MedicalCase, section: str, data: dict):
    """Apply an update to a specific section."""
    if section == "chiefComplaint":
        case.chief_complaint = data
    elif section == "vitals":
        case.vitals = data
    elif section == "clinicalNotes":
        if data.get("action") == "create":
            note = CaseNote(id=uuid4(), case_id=case.id, **data.get("data", {}))
            db.add(note)
    elif section == "treatmentPlan":
        if case.treatment_plan:
            for key, value in data.items():
                setattr(case.treatment_plan, key, value)
    elif section == "aiAnalysis":
        if data.get("rerun"):
            # Trigger AI analysis rerun
            pass
        else:
            case.ai_analysis = data


async def apply_snapshot(db: AsyncSession, case: MedicalCase, snapshot: dict):
    """Apply a snapshot to restore case state."""
    for section, data in snapshot.items():
        await apply_section_update(db, case, section, data)


def case_to_detail(case: MedicalCase) -> dict:
    """Convert case model to detail response."""
    return {
        "id": str(case.id),
        "caseNumber": case.case_number,
        "status": case.status.value if case.status else "pending",
        "priority": case.urgency_level.value if case.urgency_level else "moderate",
        "createdAt": case.created_at.isoformat(),
        "updatedAt": case.updated_at.isoformat(),
        "completedAt": case.completed_at.isoformat() if case.completed_at else None,
        "patient": patient_to_detail(case.patient),
        "assignedTo": doctor_to_detail(case.assigned_doctor),
        "createdBy": doctor_to_detail(case.created_by_doctor),
        "careTeam": [doctor_to_detail(d) for d in (case.care_team or [])],
        "chiefComplaint": case.chief_complaint,
        "vitals": case.vitals,
        "symptoms": [{"id": str(s.id), **s.__dict__} for s in (case.symptoms or [])],
        "medications": [{"id": str(m.id), **m.__dict__} for m in (case.medications or [])],
        "images": [{"id": str(i.id), **i.__dict__} for i in (case.images or [])],
        "labResults": case.lab_results or [],
        "clinicalNotes": [{"id": str(n.id), **n.__dict__} for n in (case.notes or [])],
        "treatmentPlan": case.treatment_plan.__dict__ if case.treatment_plan else None,
        "aiAnalysis": case.ai_analysis,
        "timeline": [],  # Fetched separately
        "comments": [],  # Fetched separately
        "documents": [],  # Would be fetched
    }


def patient_to_detail(patient: Patient | None) -> dict | None:
    if not patient:
        return None
    return {
        "id": str(patient.id),
        "mrn": patient.mrn,
        "firstName": patient.first_name,
        "lastName": patient.last_name,
        "fullName": f"{patient.first_name} {patient.last_name}",
        "dateOfBirth": patient.date_of_birth.isoformat(),
        "age": calculate_age(patient.date_of_birth),
        "gender": patient.gender,
        "bloodType": getattr(patient, "blood_type", None),
        "contactPhone": patient.phone_primary,
    }


def doctor_to_detail(doctor: User | None) -> dict | None:
    if not doctor:
        return None
    return {
        "id": str(doctor.id),
        "firstName": doctor.first_name,
        "lastName": doctor.last_name,
        "fullName": f"{doctor.first_name} {doctor.last_name}",
        "specialty": getattr(doctor, "specialty", "General"),
        "title": "Dr.",
        "email": doctor.email,
    }


def calculate_age(dob: datetime) -> int:
    today = datetime.now()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def audit_to_timeline_event(log: CaseAuditLog) -> dict:
    return {
        "id": str(log.id),
        "type": log.action,
        "title": format_action_title(log.action),
        "description": log.details.get("description") if log.details else None,
        "timestamp": log.timestamp.isoformat(),
        "actor": doctor_to_detail(log.actor) if log.actor else None,
        "metadata": log.details,
    }


def format_action_title(action: str) -> str:
    titles = {
        "viewed": "Case viewed",
        "updated": "Case updated",
        "comment_added": "Comment added",
        "note_added": "Clinical note added",
        "exported": "Case exported",
        "reverted": "Case reverted to previous version",
        "assigned": "Case assigned",
        "status_changed": "Status changed",
    }
    return titles.get(action, action.replace("_", " ").title())


def comment_to_thread(comment: CaseComment) -> dict:
    return {
        "id": str(comment.id),
        "sectionId": comment.section_id,
        "sectionType": comment.section_type,
        "isResolved": comment.is_resolved,
        "createdAt": comment.created_at.isoformat(),
        "comments": [
            {
                "id": str(comment.id),
                "content": comment.content,
                "author": doctor_to_detail(comment.author),
                "createdAt": comment.created_at.isoformat(),
                "isEdited": comment.is_edited,
                "mentions": comment.mentions or [],
            }
        ]
        + [
            {
                "id": str(r.id),
                "content": r.content,
                "author": doctor_to_detail(r.author),
                "createdAt": r.created_at.isoformat(),
                "isEdited": r.is_edited,
                "mentions": r.mentions or [],
                "parentId": str(comment.id),
            }
            for r in (comment.replies or [])
        ],
    }


def version_to_response(version: CaseVersion) -> dict:
    return {
        "id": str(version.id),
        "version": version.version,
        "section": version.section,
        "timestamp": version.timestamp.isoformat(),
        "author": doctor_to_detail(version.author),
        "changeType": "update",
        "changes": [],  # Would compute from snapshot diff
    }


def compute_diff(v1_data: dict, v2_data: dict) -> list:
    """Compute differences between two versions."""
    diff = []
    all_keys = set(v1_data.keys()) | set(v2_data.keys())

    for key in all_keys:
        old_val = v1_data.get(key)
        new_val = v2_data.get(key)
        if old_val != new_val:
            diff.append(
                {
                    "field": key,
                    "oldValue": old_val,
                    "newValue": new_val,
                }
            )

    return diff


async def broadcast_case_update(case_id: UUID, section: str, user_id: UUID):
    """Broadcast case update via WebSocket."""
    # Would integrate with WebSocket manager
    pass


async def notify_mentioned_users(
    case_id: UUID, comment_id: UUID, user_ids: list[str], mentioned_by: UUID
):
    """Notify users mentioned in a comment."""
    # Would send notifications
    pass


async def generate_case_docx(case: MedicalCase, options: ExportOptions) -> bytes:
    """Generate DOCX export."""
    # Would use python-docx
    return b""


async def generate_case_html(case: MedicalCase, options: ExportOptions) -> bytes:
    """Generate HTML export."""
    # Would generate HTML template
    return b""
