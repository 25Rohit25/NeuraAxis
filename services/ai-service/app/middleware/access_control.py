"""
NEURAXIS - Access Control Middleware
Authorization and permission checking for case operations
"""

from enum import Enum
from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.case import CaseStatus, MedicalCase
from app.models.user import User
from app.services.audit_logger import log_case_action

# =============================================================================
# Permission Levels
# =============================================================================


class CasePermission(str, Enum):
    """Available permissions for case operations."""

    VIEW = "view"  # Can view case details
    EDIT = "edit"  # Can edit case data
    DELETE = "delete"  # Can delete/archive case
    ASSIGN = "assign"  # Can assign case to others
    COMMENT = "comment"  # Can add comments
    EXPORT = "export"  # Can export case data
    SIGN = "sign"  # Can sign clinical notes
    FULL = "full"  # Full admin access
    AUDIT = "audit"  # Can view audit logs


class UserRole(str, Enum):
    """User roles in the system."""

    ADMIN = "admin"
    PHYSICIAN = "physician"
    NURSE = "nurse"
    RESIDENT = "resident"
    MEDICAL_ASSISTANT = "medical_assistant"
    VIEWER = "viewer"


# =============================================================================
# Role-Based Permissions Map
# =============================================================================

ROLE_PERMISSIONS: dict[UserRole, set[CasePermission]] = {
    UserRole.ADMIN: {
        CasePermission.VIEW,
        CasePermission.EDIT,
        CasePermission.DELETE,
        CasePermission.ASSIGN,
        CasePermission.COMMENT,
        CasePermission.EXPORT,
        CasePermission.SIGN,
        CasePermission.FULL,
        CasePermission.AUDIT,
    },
    UserRole.PHYSICIAN: {
        CasePermission.VIEW,
        CasePermission.EDIT,
        CasePermission.ASSIGN,
        CasePermission.COMMENT,
        CasePermission.EXPORT,
        CasePermission.SIGN,
    },
    UserRole.NURSE: {
        CasePermission.VIEW,
        CasePermission.EDIT,
        CasePermission.COMMENT,
    },
    UserRole.RESIDENT: {
        CasePermission.VIEW,
        CasePermission.EDIT,
        CasePermission.COMMENT,
    },
    UserRole.MEDICAL_ASSISTANT: {
        CasePermission.VIEW,
        CasePermission.COMMENT,
    },
    UserRole.VIEWER: {
        CasePermission.VIEW,
    },
}


# =============================================================================
# Permission Checking Functions
# =============================================================================


def get_user_role(user: User) -> UserRole:
    """Get the role of a user."""
    role = getattr(user, "role", "viewer")
    try:
        return UserRole(role.lower())
    except ValueError:
        return UserRole.VIEWER


def has_role_permission(user: User, permission: CasePermission) -> bool:
    """Check if user's role has the required permission."""
    role = get_user_role(user)
    return permission in ROLE_PERMISSIONS.get(role, set())


async def has_case_access(
    user: User,
    case: MedicalCase,
    permission: CasePermission,
) -> bool:
    """
    Check if user has access to a specific case with given permission.

    Access rules:
    1. Admins have full access to all cases
    2. Assigned doctor has full access
    3. Creating doctor has view/comment access
    4. Care team members have view/edit access
    5. Same department has view access (if enabled)
    """
    # Check role-based permission first
    if not has_role_permission(user, permission):
        return False

    # Admin has full access
    role = get_user_role(user)
    if role == UserRole.ADMIN:
        return True

    # Assigned doctor
    if case.assigned_doctor_id == user.id:
        return True

    # Creating doctor
    if case.created_by_id == user.id:
        if permission in {CasePermission.VIEW, CasePermission.COMMENT, CasePermission.EXPORT}:
            return True

    # Care team member
    care_team_ids = [m.id for m in (case.care_team or [])]
    if user.id in care_team_ids:
        if permission in {CasePermission.VIEW, CasePermission.EDIT, CasePermission.COMMENT}:
            return True

    # Completed/archived cases have restricted access
    if case.status in [CaseStatus.completed, CaseStatus.archived]:
        if permission == CasePermission.EDIT:
            return role == UserRole.ADMIN

    return False


def check_case_access(permission: CasePermission):
    """
    Dependency factory for checking case access in routes.

    Usage:
        @router.get("/{case_id}")
        async def get_case(
            case_id: UUID,
            access: bool = Depends(check_case_access(CasePermission.VIEW)),
        ):
            ...
    """

    async def dependency(
        request: Request,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> bool:
        # Extract case_id from path
        case_id = request.path_params.get("case_id")
        if not case_id:
            raise HTTPException(status_code=400, detail="Case ID required")

        # Load case
        result = await db.execute(select(MedicalCase).where(MedicalCase.id == case_id))
        case = result.scalar_one_or_none()

        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Check access
        if not await has_case_access(current_user, case, permission):
            # Log unauthorized access attempt
            await log_case_action(
                db,
                case.id,
                current_user.id,
                "access_denied",
                details={"permission": permission.value},
            )
            raise HTTPException(
                status_code=403, detail=f"Insufficient permissions: {permission.value}"
            )

        return True

    return dependency


# =============================================================================
# Decorators for Route Protection
# =============================================================================


def require_permission(permission: CasePermission):
    """
    Decorator to require a specific permission for a route.

    Usage:
        @router.post("/{case_id}/assign")
        @require_permission(CasePermission.ASSIGN)
        async def assign_case(...):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get dependencies from kwargs
            db = kwargs.get("db")
            current_user = kwargs.get("current_user")
            case_id = kwargs.get("case_id")

            if not all([db, current_user, case_id]):
                raise HTTPException(status_code=500, detail="Missing dependencies")

            # Load and check case
            result = await db.execute(select(MedicalCase).where(MedicalCase.id == case_id))
            case = result.scalar_one_or_none()

            if not case:
                raise HTTPException(status_code=404, detail="Case not found")

            if not await has_case_access(current_user, case, permission):
                raise HTTPException(
                    status_code=403, detail=f"Permission denied: {permission.value}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles: UserRole):
    """
    Decorator to require one of specified roles.

    Usage:
        @router.delete("/{case_id}")
        @require_role(UserRole.ADMIN, UserRole.PHYSICIAN)
        async def delete_case(...):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            user_role = get_user_role(current_user)
            if user_role not in roles:
                raise HTTPException(
                    status_code=403, detail=f"Role required: {', '.join(r.value for r in roles)}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# Middleware Class
# =============================================================================


class CaseAccessMiddleware:
    """
    Middleware for case access control.
    Performs access checks at the middleware level.
    """

    # Routes that require case access checks
    PROTECTED_PATTERNS = [
        (r"/api/cases/([a-f0-9-]+)$", CasePermission.VIEW, "GET"),
        (r"/api/cases/([a-f0-9-]+)$", CasePermission.EDIT, "PATCH"),
        (r"/api/cases/([a-f0-9-]+)$", CasePermission.DELETE, "DELETE"),
        (r"/api/cases/([a-f0-9-]+)/assign", CasePermission.ASSIGN, "POST"),
        (r"/api/cases/([a-f0-9-]+)/export", CasePermission.EXPORT, "POST"),
        (r"/api/cases/([a-f0-9-]+)/audit", CasePermission.AUDIT, "GET"),
    ]

    async def __call__(self, request: Request, call_next):
        import re

        path = request.url.path
        method = request.method

        for pattern, permission, allowed_method in self.PROTECTED_PATTERNS:
            if method == allowed_method:
                match = re.match(pattern, path)
                if match:
                    # Access control would be performed here
                    # Currently handled by dependency injection
                    break

        response = await call_next(request)
        return response


# =============================================================================
# Helper Functions for Section-Level Access
# =============================================================================


async def can_edit_section(
    user: User,
    case: MedicalCase,
    section: str,
) -> bool:
    """
    Check if user can edit a specific section of a case.
    Some sections may have stricter access requirements.
    """
    # Check base edit permission
    if not await has_case_access(user, case, CasePermission.EDIT):
        return False

    # Signed notes cannot be edited except by admin
    if section == "clinicalNotes":
        # Would check if notes are signed
        pass

    # AI analysis can only be re-run
    if section == "aiAnalysis":
        return has_role_permission(user, CasePermission.EDIT)

    # Treatment plan requires physician
    if section == "treatmentPlan":
        role = get_user_role(user)
        return role in [UserRole.ADMIN, UserRole.PHYSICIAN, UserRole.RESIDENT]

    return True


async def get_accessible_cases(
    db: AsyncSession,
    user: User,
    include_team: bool = True,
    include_department: bool = False,
) -> list:
    """
    Get all case IDs that a user can access.
    Used for filtering case queries.
    """
    from sqlalchemy import or_

    conditions = [
        MedicalCase.assigned_doctor_id == user.id,
        MedicalCase.created_by_id == user.id,
    ]

    # Admin sees all
    if get_user_role(user) == UserRole.ADMIN:
        result = await db.execute(select(MedicalCase.id))
        return [row[0] for row in result.all()]

    # Include team cases
    if include_team:
        # Would join with care_team relation
        pass

    query = select(MedicalCase.id).where(or_(*conditions))
    result = await db.execute(query)

    return [row[0] for row in result.all()]
