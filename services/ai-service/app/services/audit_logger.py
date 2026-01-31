"""
NEURAXIS - Audit Logger Service
Comprehensive audit logging for case actions
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import CaseAuditLog


async def log_case_action(
    db: AsyncSession,
    case_id: UUID,
    user_id: UUID,
    action: str,
    section: Optional[str] = None,
    details: Optional[dict] = None,
) -> CaseAuditLog:
    """
    Log an action performed on a medical case.

    Args:
        db: Database session
        case_id: ID of the case being acted upon
        user_id: ID of the user performing the action
        action: Type of action (viewed, updated, exported, etc.)
        section: Optional section of the case affected
        details: Optional dictionary with additional details

    Returns:
        The created audit log entry
    """
    log_entry = CaseAuditLog(
        id=uuid4(),
        case_id=case_id,
        actor_id=user_id,
        action=action,
        section=section,
        details=details or {},
        timestamp=datetime.now(),
        ip_address=None,  # Would be set from request context
        user_agent=None,  # Would be set from request context
    )

    db.add(log_entry)
    await db.commit()

    return log_entry


async def get_case_audit_trail(
    db: AsyncSession,
    case_id: UUID,
    limit: int = 100,
    offset: int = 0,
    action_filter: Optional[str] = None,
) -> list[CaseAuditLog]:
    """
    Retrieve audit trail for a specific case.

    Args:
        db: Database session
        case_id: ID of the case
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        action_filter: Optional filter for specific action types

    Returns:
        List of audit log entries
    """
    query = (
        select(CaseAuditLog)
        .where(CaseAuditLog.case_id == case_id)
        .order_by(CaseAuditLog.timestamp.desc())
    )

    if action_filter:
        query = query.where(CaseAuditLog.action == action_filter)

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_activity(
    db: AsyncSession,
    user_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> list[CaseAuditLog]:
    """
    Get all actions performed by a specific user.

    Args:
        db: Database session
        user_id: ID of the user
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of entries

    Returns:
        List of audit log entries
    """
    query = (
        select(CaseAuditLog)
        .where(CaseAuditLog.actor_id == user_id)
        .order_by(CaseAuditLog.timestamp.desc())
    )

    if start_date:
        query = query.where(CaseAuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(CaseAuditLog.timestamp <= end_date)

    query = query.limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def log_data_export(
    db: AsyncSession,
    user_id: UUID,
    case_ids: list[UUID],
    export_format: str,
    export_type: str = "single_case",
) -> CaseAuditLog:
    """
    Log a data export action for compliance tracking.

    Args:
        db: Database session
        user_id: ID of user performing export
        case_ids: List of case IDs being exported
        export_format: Format of export (pdf, docx, csv, etc.)
        export_type: Type of export (single_case, bulk, report)

    Returns:
        The created audit log entry
    """
    # Log for each case
    entries = []
    for case_id in case_ids:
        entry = await log_case_action(
            db=db,
            case_id=case_id,
            user_id=user_id,
            action="exported",
            details={
                "format": export_format,
                "export_type": export_type,
                "case_count": len(case_ids),
            },
        )
        entries.append(entry)

    return entries[0] if entries else None


async def log_phi_access(
    db: AsyncSession,
    case_id: UUID,
    user_id: UUID,
    accessed_fields: list[str],
    access_reason: Optional[str] = None,
):
    """
    Log access to Protected Health Information (PHI) for HIPAA compliance.

    Args:
        db: Database session
        case_id: ID of case containing PHI
        user_id: ID of user accessing PHI
        accessed_fields: List of PHI fields accessed
        access_reason: Optional reason for access
    """
    await log_case_action(
        db=db,
        case_id=case_id,
        user_id=user_id,
        action="phi_accessed",
        details={
            "accessed_fields": accessed_fields,
            "access_reason": access_reason,
            "compliance_log": True,
        },
    )


class AuditContext:
    """
    Context manager for batch audit logging.
    Collects multiple actions and logs them together.
    """

    def __init__(self, db: AsyncSession, user_id: UUID, case_id: UUID):
        self.db = db
        self.user_id = user_id
        self.case_id = case_id
        self.actions: list[dict] = []

    def add_action(
        self,
        action: str,
        section: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        """Add an action to be logged."""
        self.actions.append(
            {
                "action": action,
                "section": section,
                "details": details,
            }
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Log all collected actions
        if not exc_type:
            for action_data in self.actions:
                await log_case_action(
                    db=self.db, case_id=self.case_id, user_id=self.user_id, **action_data
                )
        return False
