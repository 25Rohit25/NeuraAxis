"""
NEURAXIS - JWT Token Utilities
==============================
Secure JWT token generation, validation, and management.
Supports access tokens, refresh tokens, and password reset tokens.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID

import jwt
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()


# ============================================================================
# TOKEN TYPES & CONFIGURATION
# ============================================================================


class TokenType(str, Enum):
    """Types of JWT tokens."""

    ACCESS = "access"
    REFRESH = "refresh"
    RESET_PASSWORD = "reset_password"
    EMAIL_VERIFICATION = "email_verification"
    MFA_SETUP = "mfa_setup"


@dataclass
class TokenConfig:
    """Configuration for different token types."""

    expiry_minutes: int
    algorithm: str = "HS256"


# Token configurations
TOKEN_CONFIGS: dict[TokenType, TokenConfig] = {
    TokenType.ACCESS: TokenConfig(
        expiry_minutes=15,  # 15 minutes for access tokens
        algorithm="HS256",
    ),
    TokenType.REFRESH: TokenConfig(
        expiry_minutes=60 * 24 * 7,  # 7 days for refresh tokens
        algorithm="HS256",
    ),
    TokenType.RESET_PASSWORD: TokenConfig(
        expiry_minutes=60,  # 1 hour for password reset
        algorithm="HS256",
    ),
    TokenType.EMAIL_VERIFICATION: TokenConfig(
        expiry_minutes=60 * 24,  # 24 hours for email verification
        algorithm="HS256",
    ),
    TokenType.MFA_SETUP: TokenConfig(
        expiry_minutes=10,  # 10 minutes for MFA setup
        algorithm="HS256",
    ),
}


# ============================================================================
# TOKEN PAYLOAD MODELS
# ============================================================================


class AccessTokenPayload(BaseModel):
    """Payload for access tokens."""

    sub: str  # User ID
    email: str
    role: str
    organization_id: str
    permissions: list[str]
    session_id: str
    type: str = "access"
    iat: datetime
    exp: datetime


class RefreshTokenPayload(BaseModel):
    """Payload for refresh tokens."""

    sub: str  # User ID
    session_id: str
    type: str = "refresh"
    iat: datetime
    exp: datetime


class ResetPasswordPayload(BaseModel):
    """Payload for password reset tokens."""

    sub: str  # User ID
    email: str
    type: str = "reset_password"
    iat: datetime
    exp: datetime


# ============================================================================
# EXCEPTIONS
# ============================================================================


class TokenError(Exception):
    """Base exception for token errors."""

    pass


class TokenExpiredError(TokenError):
    """Token has expired."""

    pass


class TokenInvalidError(TokenError):
    """Token is invalid or malformed."""

    pass


class TokenRevokedError(TokenError):
    """Token has been revoked."""

    pass


# ============================================================================
# TOKEN CREATION
# ============================================================================


def create_access_token(
    user_id: str | UUID,
    email: str,
    role: str,
    organization_id: str | UUID,
    permissions: list[str],
    session_id: str | UUID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a new access token.

    Args:
        user_id: User's UUID
        email: User's email
        role: User's role
        organization_id: User's organization UUID
        permissions: List of permission strings
        session_id: Session UUID
        expires_delta: Custom expiration time

    Returns:
        Encoded JWT access token
    """
    config = TOKEN_CONFIGS[TokenType.ACCESS]

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.expiry_minutes)

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "organization_id": str(organization_id),
        "permissions": permissions,
        "session_id": str(session_id),
        "type": TokenType.ACCESS.value,
        "iat": now,
        "exp": expire,
        "jti": secrets.token_hex(16),  # JWT ID for uniqueness
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=config.algorithm,
    )


def create_refresh_token(
    user_id: str | UUID,
    session_id: str | UUID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a new refresh token.

    Args:
        user_id: User's UUID
        session_id: Session UUID
        expires_delta: Custom expiration time

    Returns:
        Encoded JWT refresh token
    """
    config = TOKEN_CONFIGS[TokenType.REFRESH]

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=config.expiry_minutes)

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "session_id": str(session_id),
        "type": TokenType.REFRESH.value,
        "iat": now,
        "exp": expire,
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=config.algorithm,
    )


def create_token_pair(
    user_id: str | UUID,
    email: str,
    role: str,
    organization_id: str | UUID,
    permissions: list[str],
    session_id: str | UUID,
) -> tuple[str, str, int]:
    """
    Create both access and refresh tokens.

    Returns:
        Tuple of (access_token, refresh_token, expires_in_seconds)
    """
    access_token = create_access_token(
        user_id=user_id,
        email=email,
        role=role,
        organization_id=organization_id,
        permissions=permissions,
        session_id=session_id,
    )

    refresh_token = create_refresh_token(
        user_id=user_id,
        session_id=session_id,
    )

    config = TOKEN_CONFIGS[TokenType.ACCESS]
    expires_in = config.expiry_minutes * 60  # Convert to seconds

    return access_token, refresh_token, expires_in


def create_password_reset_token(
    user_id: str | UUID,
    email: str,
) -> str:
    """
    Create a password reset token.

    Args:
        user_id: User's UUID
        email: User's email

    Returns:
        Encoded JWT reset token
    """
    config = TOKEN_CONFIGS[TokenType.RESET_PASSWORD]
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.expiry_minutes)
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "email": email,
        "type": TokenType.RESET_PASSWORD.value,
        "iat": now,
        "exp": expire,
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=config.algorithm,
    )


def create_email_verification_token(
    user_id: str | UUID,
    email: str,
) -> str:
    """
    Create an email verification token.

    Args:
        user_id: User's UUID
        email: User's email

    Returns:
        Encoded JWT verification token
    """
    config = TOKEN_CONFIGS[TokenType.EMAIL_VERIFICATION]
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.expiry_minutes)
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "email": email,
        "type": TokenType.EMAIL_VERIFICATION.value,
        "iat": now,
        "exp": expire,
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=config.algorithm,
    )


# ============================================================================
# TOKEN VERIFICATION
# ============================================================================


def decode_token(
    token: str,
    expected_type: Optional[TokenType] = None,
    verify_exp: bool = True,
) -> dict[str, Any]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string
        expected_type: Expected token type (if specified, will validate)
        verify_exp: Whether to verify expiration

    Returns:
        Decoded token payload

    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid or malformed
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"],
            options={
                "verify_exp": verify_exp,
                "require": ["sub", "type", "iat", "exp"],
            },
        )

        # Validate token type if specified
        if expected_type and payload.get("type") != expected_type.value:
            raise TokenInvalidError(
                f"Invalid token type. Expected {expected_type.value}, got {payload.get('type')}"
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise TokenInvalidError(f"Invalid token: {str(e)}")


def verify_access_token(token: str) -> AccessTokenPayload:
    """
    Verify and decode an access token.

    Args:
        token: JWT access token

    Returns:
        AccessTokenPayload with decoded data
    """
    payload = decode_token(token, expected_type=TokenType.ACCESS)

    return AccessTokenPayload(
        sub=payload["sub"],
        email=payload["email"],
        role=payload["role"],
        organization_id=payload["organization_id"],
        permissions=payload.get("permissions", []),
        session_id=payload["session_id"],
        type=payload["type"],
        iat=datetime.fromisoformat(payload["iat"])
        if isinstance(payload["iat"], str)
        else payload["iat"],
        exp=datetime.fromisoformat(payload["exp"])
        if isinstance(payload["exp"], str)
        else payload["exp"],
    )


def verify_refresh_token(token: str) -> RefreshTokenPayload:
    """
    Verify and decode a refresh token.

    Args:
        token: JWT refresh token

    Returns:
        RefreshTokenPayload with decoded data
    """
    payload = decode_token(token, expected_type=TokenType.REFRESH)

    return RefreshTokenPayload(
        sub=payload["sub"],
        session_id=payload["session_id"],
        type=payload["type"],
        iat=datetime.fromisoformat(payload["iat"])
        if isinstance(payload["iat"], str)
        else payload["iat"],
        exp=datetime.fromisoformat(payload["exp"])
        if isinstance(payload["exp"], str)
        else payload["exp"],
    )


def verify_password_reset_token(token: str) -> ResetPasswordPayload:
    """
    Verify and decode a password reset token.

    Args:
        token: JWT reset token

    Returns:
        ResetPasswordPayload with decoded data
    """
    payload = decode_token(token, expected_type=TokenType.RESET_PASSWORD)

    return ResetPasswordPayload(
        sub=payload["sub"],
        email=payload["email"],
        type=payload["type"],
        iat=datetime.fromisoformat(payload["iat"])
        if isinstance(payload["iat"], str)
        else payload["iat"],
        exp=datetime.fromisoformat(payload["exp"])
        if isinstance(payload["exp"], str)
        else payload["exp"],
    )


# ============================================================================
# TOKEN UTILITIES
# ============================================================================


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get the expiry time of a token without full verification.

    Args:
        token: JWT token

    Returns:
        Expiry datetime or None if invalid
    """
    try:
        # Decode without verification to get expiry
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
        )
        exp = payload.get("exp")
        if exp:
            if isinstance(exp, (int, float)):
                return datetime.fromtimestamp(exp, tz=timezone.utc)
            return datetime.fromisoformat(exp)
        return None
    except jwt.InvalidTokenError:
        return None


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired.

    Args:
        token: JWT token

    Returns:
        True if expired, False otherwise
    """
    expiry = get_token_expiry(token)
    if expiry is None:
        return True
    return datetime.now(timezone.utc) > expiry


def get_token_remaining_time(token: str) -> int:
    """
    Get remaining time until token expires in seconds.

    Args:
        token: JWT token

    Returns:
        Remaining seconds (negative if expired)
    """
    expiry = get_token_expiry(token)
    if expiry is None:
        return -1

    delta = expiry - datetime.now(timezone.utc)
    return int(delta.total_seconds())


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from token without full verification.
    Useful for logging when token might be invalid.

    Args:
        token: JWT token

    Returns:
        User ID string or None
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
        )
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None
