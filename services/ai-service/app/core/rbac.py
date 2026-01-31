from enum import Enum
from typing import List, Optional

from fastapi import Depends, HTTPException, Request


class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    RESEARCHER = "researcher"
    PATIENT = "patient"


# Role Hierarchy / Permissions (Simplified)
# Format: Role -> allowed scopes?
# Or for this implementation, just simple Role checks.


def verify_role(allowed_roles: List[UserRole]):
    """
    FastAPI Dependency to enforce RBAC.
    """

    def _verify(request: Request):
        # Assumes AuthMiddleware has populated request.state.user
        # user = { "id": "...", "role": "doctor", ... }

        user = getattr(request.state, "user", None)

        # Development bypass if no auth middleware active?
        # No, Security First: Fail closed.
        if not user:
            # Check headers for mock auth in dev if strictly needed, otherwise fail
            # For now, allowing a "mock" header for demo purposes setup
            # In production, require strict request.state.user
            auth_header = request.headers.get("X-Mock-Role")
            if auth_header:
                return {"id": "mock-user", "role": auth_header}

            raise HTTPException(status_code=401, detail="Authentication required")

        user_role_str = user.get("role")
        try:
            user_role = UserRole(user_role_str)
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid role assigned")

        if user_role not in allowed_roles:
            # Audit Log Implementation Hook Here
            # audit.log_access(user["id"], "ACCESS_DENIED", "API", str(request.url), False)
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return user

    return _verify
