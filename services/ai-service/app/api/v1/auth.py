"""
NEURAXIS - FastAPI Authentication Routes
=========================================
Complete authentication API with login, MFA, password reset, and session management.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field

from app.core.config import get_settings
from app.services.mfa import setup_mfa, verify_mfa_code
from app.utils.jwt import (
    TokenExpiredError,
    TokenInvalidError,
    create_password_reset_token,
    create_token_pair,
    verify_access_token,
    verify_password_reset_token,
)
from app.utils.password import (
    HIPAA_PASSWORD_REQUIREMENTS,
    generate_reset_token,
    hash_password,
    validate_password,
    verify_password,
)

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)
    mfa_code: Optional[str] = None
    remember_me: bool = False


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12)
    confirm_password: str
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    organization_id: Optional[UUID] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    organization_id: str
    mfa_enabled: bool


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None
    tokens: Optional[TokenResponse] = None
    mfa_required: bool = False
    session_id: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12)
    confirm_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)
    confirm_password: str


class MFASetupResponse(BaseModel):
    secret: str
    qr_code_url: str
    provisioning_uri: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=10)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ============================================================================
# MOCK USER DATA (Replace with database in production)
# ============================================================================

MOCK_USERS = {
    "doctor@neuraxis.health": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "email": "doctor@neuraxis.health",
        "password_hash": hash_password("SecurePass123!"),
        "first_name": "Sarah",
        "last_name": "Johnson",
        "role": "doctor",
        "organization_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "active",
        "mfa_enabled": False,
        "mfa_secret_encrypted": None,
        "backup_codes_hashed": None,
        "failed_login_attempts": 0,
        "locked_until": None,
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "unknown")[:500]


async def log_auth_event(
    event_type: str,
    email: Optional[str] = None,
    user_id: Optional[str] = None,
    success: bool = True,
    ip_address: str = "",
    user_agent: str = "",
    error_message: Optional[str] = None,
):
    """Log authentication events for audit trail."""
    print(f"[AUDIT] {event_type}: email={email}, success={success}, ip={ip_address}")


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, data: LoginRequest):
    """
    Authenticate user with email/password.
    Returns MFA challenge if MFA is enabled.
    """
    ip = get_client_ip(request)
    ua = get_user_agent(request)

    # Get user
    user = MOCK_USERS.get(data.email.lower())
    if not user:
        await log_auth_event(
            "login_failed", data.email, success=False, ip_address=ip, user_agent=ua
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check lockout
    if user.get("locked_until"):
        lock_time = datetime.fromisoformat(user["locked_until"])
        if datetime.now(timezone.utc) < lock_time:
            raise HTTPException(status_code=423, detail="Account locked. Try again later.")

    # Verify password
    if not verify_password(data.password, user["password_hash"]):
        user["failed_login_attempts"] = user.get("failed_login_attempts", 0) + 1
        if user["failed_login_attempts"] >= 5:
            user["locked_until"] = (datetime.now(timezone.utc).replace(minute=30)).isoformat()
        await log_auth_event("login_failed", data.email, success=False, ip_address=ip)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check MFA
    if user.get("mfa_enabled") and user.get("mfa_secret_encrypted"):
        if not data.mfa_code:
            return LoginResponse(
                success=False,
                message="MFA verification required",
                mfa_required=True,
            )
        result = verify_mfa_code(
            data.mfa_code, user["mfa_secret_encrypted"], user.get("backup_codes_hashed")
        )
        if not result.success:
            await log_auth_event("mfa_failed", data.email, success=False, ip_address=ip)
            raise HTTPException(status_code=401, detail="Invalid MFA code")

    # Success - reset failed attempts
    user["failed_login_attempts"] = 0
    user["locked_until"] = None

    # Generate tokens
    session_id = "session-" + generate_reset_token(16)
    access_token, refresh_token, expires_in = create_token_pair(
        user_id=user["id"],
        email=user["email"],
        role=user["role"],
        organization_id=user["organization_id"],
        permissions=["patient:read", "diagnosis:read"],
        session_id=session_id,
    )

    await log_auth_event("login_success", data.email, user["id"], True, ip, ua)

    return LoginResponse(
        success=True,
        message="Login successful",
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            role=user["role"],
            organization_id=user["organization_id"],
            mfa_enabled=user.get("mfa_enabled", False),
        ),
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        ),
        session_id=session_id,
    )


@router.post("/register", status_code=201)
async def register(request: Request, data: RegisterRequest):
    """Register a new user account."""
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Validate password
    validation = validate_password(
        data.password,
        HIPAA_PASSWORD_REQUIREMENTS,
        data.email,
        data.first_name,
        data.last_name,
    )
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail={"errors": validation.errors})

    if data.email.lower() in MOCK_USERS:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create user
    user_id = f"550e8400-e29b-41d4-a716-{len(MOCK_USERS):012d}"
    MOCK_USERS[data.email.lower()] = {
        "id": user_id,
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "first_name": data.first_name,
        "last_name": data.last_name,
        "role": "patient",
        "organization_id": str(data.organization_id) if data.organization_id else "default-org",
        "status": "pending_verification",
        "mfa_enabled": False,
    }

    return {"success": True, "message": "Registration successful", "user_id": user_id}


@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Logout and invalidate session."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = verify_access_token(credentials.credentials)
        await log_auth_event("logout", payload.email, payload.sub, True, get_client_ip(request))
        return {"success": True, "message": "Logged out successfully"}
    except (TokenExpiredError, TokenInvalidError):
        return {"success": True, "message": "Session already expired"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    from app.utils.jwt import verify_refresh_token

    try:
        payload = verify_refresh_token(data.refresh_token)
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except TokenInvalidError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Find user
    user = None
    for u in MOCK_USERS.values():
        if u["id"] == payload.sub:
            user = u
            break

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token, refresh_token, expires_in = create_token_pair(
        user_id=user["id"],
        email=user["email"],
        role=user["role"],
        organization_id=user["organization_id"],
        permissions=["patient:read"],
        session_id=payload.session_id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post("/password/reset-request")
async def request_password_reset(data: PasswordResetRequest):
    """Request password reset email."""
    user = MOCK_USERS.get(data.email.lower())
    # Always return success to prevent email enumeration
    if user:
        token = create_password_reset_token(user["id"], user["email"])
        print(f"[EMAIL] Password reset token for {data.email}: {token[:20]}...")

    return {"success": True, "message": "If email exists, reset instructions sent"}


@router.post("/password/reset")
async def reset_password(data: PasswordResetConfirm):
    """Reset password using token."""
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        payload = verify_password_reset_token(data.token)
    except TokenExpiredError:
        raise HTTPException(status_code=400, detail="Reset token expired")
    except TokenInvalidError:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    user = MOCK_USERS.get(payload.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    validation = validate_password(data.new_password, HIPAA_PASSWORD_REQUIREMENTS, payload.email)
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail={"errors": validation.errors})

    user["password_hash"] = hash_password(data.new_password)
    user["failed_login_attempts"] = 0
    user["locked_until"] = None

    return {"success": True, "message": "Password reset successful"}


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_user_mfa(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Initialize MFA setup for authenticated user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_access_token(credentials.credentials)
    user = None
    for u in MOCK_USERS.values():
        if u["id"] == payload.sub:
            user = u
            break

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    mfa_data = setup_mfa(user["email"])
    user["mfa_secret_encrypted"] = mfa_data.secret_encrypted
    user["backup_codes_hashed"] = mfa_data.backup_codes_hashed

    return MFASetupResponse(
        secret=mfa_data.secret,
        qr_code_url=mfa_data.qr_code_url,
        provisioning_uri=mfa_data.provisioning_uri,
        backup_codes=mfa_data.backup_codes,
    )


@router.post("/mfa/verify")
async def verify_mfa_setup(
    data: MFAVerifyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Verify MFA setup with code from authenticator app."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_access_token(credentials.credentials)
    user = None
    for u in MOCK_USERS.values():
        if u["id"] == payload.sub:
            user = u
            break

    if not user or not user.get("mfa_secret_encrypted"):
        raise HTTPException(status_code=400, detail="MFA not initialized")

    result = verify_mfa_code(data.code, user["mfa_secret_encrypted"])
    if not result.success:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user["mfa_enabled"] = True
    return {"success": True, "message": "MFA enabled successfully"}


@router.delete("/mfa")
async def disable_mfa(
    data: MFAVerifyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Disable MFA (requires current MFA code)."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_access_token(credentials.credentials)
    user = None
    for u in MOCK_USERS.values():
        if u["id"] == payload.sub:
            user = u
            break

    if not user or not user.get("mfa_enabled"):
        raise HTTPException(status_code=400, detail="MFA not enabled")

    result = verify_mfa_code(
        data.code, user["mfa_secret_encrypted"], user.get("backup_codes_hashed")
    )
    if not result.success:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user["mfa_enabled"] = False
    user["mfa_secret_encrypted"] = None
    user["backup_codes_hashed"] = None

    return {"success": True, "message": "MFA disabled"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = verify_access_token(credentials.credentials)
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Token expired")
    except TokenInvalidError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = None
    for u in MOCK_USERS.values():
        if u["id"] == payload.sub:
            user = u
            break

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user["id"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        role=user["role"],
        organization_id=user["organization_id"],
        mfa_enabled=user.get("mfa_enabled", False),
    )
