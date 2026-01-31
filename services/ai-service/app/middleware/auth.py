"""
NEURAXIS - Authentication Middleware
=====================================
FastAPI middleware and dependencies for authentication and authorization.
"""

from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.jwt import (
    AccessTokenPayload,
    TokenExpiredError,
    TokenInvalidError,
    verify_access_token,
)

security = HTTPBearer(auto_error=False)


class AuthUser:
    """Authenticated user context."""

    def __init__(self, payload: AccessTokenPayload):
        self.id = payload.sub
        self.email = payload.email
        self.role = payload.role
        self.organization_id = payload.organization_id
        self.permissions = payload.permissions
        self.session_id = payload.session_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthUser:
    """
    Dependency to get current authenticated user from JWT token.
    Raises 401 if not authenticated or token is invalid.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_access_token(credentials.credentials)
        return AuthUser(payload)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[AuthUser]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Does not raise exception for unauthenticated requests.
    """
    if not credentials:
        return None

    try:
        payload = verify_access_token(credentials.credentials)
        return AuthUser(payload)
    except (TokenExpiredError, TokenInvalidError):
        return None


def require_role(*allowed_roles: str):
    """
    Dependency factory that requires specific roles.

    Usage:
        @router.get("/admin")
        async def admin_route(user: AuthUser = Depends(require_role("admin", "super_admin"))):
            ...
    """

    async def role_checker(
        user: AuthUser = Depends(get_current_user),
    ) -> AuthUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not authorized. Required: {', '.join(allowed_roles)}",
            )
        return user

    return role_checker


def require_permission(*required_permissions: str):
    """
    Dependency factory that requires specific permissions.

    Usage:
        @router.get("/patients")
        async def list_patients(user: AuthUser = Depends(require_permission("patient:read"))):
            ...
    """

    async def permission_checker(
        user: AuthUser = Depends(get_current_user),
    ) -> AuthUser:
        user_permissions = set(user.permissions)
        required = set(required_permissions)

        if not required.issubset(user_permissions):
            missing = required - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
        return user

    return permission_checker


def require_any_permission(*required_permissions: str):
    """
    Dependency factory that requires at least one of the specified permissions.
    """

    async def permission_checker(
        user: AuthUser = Depends(get_current_user),
    ) -> AuthUser:
        user_permissions = set(user.permissions)
        required = set(required_permissions)

        if not user_permissions.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(required_permissions)}",
            )
        return user

    return permission_checker


class RoleChecker:
    """
    Class-based dependency for role checking.

    Usage:
        doctor_only = RoleChecker(["doctor", "admin"])

        @router.get("/diagnose")
        async def diagnose(user: AuthUser = Depends(doctor_only)):
            ...
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        user: AuthUser = Depends(get_current_user),
    ) -> AuthUser:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role: {user.role}",
            )
        return user


class PermissionChecker:
    """
    Class-based dependency for permission checking.
    """

    def __init__(self, required_permissions: list[str], require_all: bool = True):
        self.required_permissions = required_permissions
        self.require_all = require_all

    async def __call__(
        self,
        user: AuthUser = Depends(get_current_user),
    ) -> AuthUser:
        user_permissions = set(user.permissions)
        required = set(self.required_permissions)

        if self.require_all:
            if not required.issubset(user_permissions):
                missing = required - user_permissions
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permissions: {', '.join(missing)}",
                )
        else:
            if not user_permissions.intersection(required):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )

        return user


# Pre-configured role checkers
AdminOnly = RoleChecker(["admin", "super_admin"])
DoctorOrAbove = RoleChecker(["doctor", "admin", "super_admin"])
MedicalStaff = RoleChecker(["doctor", "nurse", "radiologist", "technician", "admin", "super_admin"])


async def verify_organization_access(
    resource_org_id: str,
    user: AuthUser = Depends(get_current_user),
) -> bool:
    """Verify user has access to a specific organization's resources."""
    if user.role == "super_admin":
        return True
    if user.organization_id != resource_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Resource belongs to different organization",
        )
    return True


def audit_access(resource_type: str, action: str):
    """
    Decorator to audit PHI access.

    Usage:
        @router.get("/patients/{patient_id}")
        @audit_access("patient", "read")
        async def get_patient(...):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user from kwargs
            request = kwargs.get("request")
            user = kwargs.get("user")

            # Log the access
            ip = "unknown"
            if request:
                forwarded = request.headers.get("X-Forwarded-For")
                ip = (
                    forwarded.split(",")[0]
                    if forwarded
                    else (request.client.host if request.client else "unknown")
                )

            user_id = user.id if user else "anonymous"
            print(f"[PHI_AUDIT] {resource_type}:{action} by user={user_id} from ip={ip}")

            return await func(*args, **kwargs)

        return wrapper

    return decorator
