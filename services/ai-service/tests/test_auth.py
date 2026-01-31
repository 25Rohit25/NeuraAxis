"""
NEURAXIS - Authentication Unit Tests
=====================================
Tests for password utilities, JWT tokens, and MFA functions.
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.utils.jwt import (
    TokenExpiredError,
    TokenInvalidError,
    TokenType,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    create_token_pair,
    get_token_remaining_time,
    is_token_expired,
    verify_access_token,
    verify_password_reset_token,
    verify_refresh_token,
)
from app.utils.password import (
    HIPAA_PASSWORD_REQUIREMENTS,
    PasswordRequirements,
    calculate_password_entropy,
    estimate_crack_time,
    generate_backup_codes,
    generate_reset_token,
    generate_temporary_password,
    hash_password,
    needs_rehash,
    validate_password,
    verify_password,
)

# ============================================================================
# PASSWORD HASHING TESTS
# ============================================================================


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """Hash function returns a string."""
        result = hash_password("TestPassword123!")
        assert isinstance(result, str)
        assert result.startswith("$2b$")

    def test_hash_password_different_outputs(self):
        """Same password produces different hashes (due to salt)."""
        hash1 = hash_password("TestPassword123!")
        hash2 = hash_password("TestPassword123!")
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Correct password verifies successfully."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password fails verification."""
        hashed = hash_password("CorrectPassword123!")
        assert verify_password("WrongPassword123!", hashed) is False

    def test_verify_password_empty(self):
        """Empty password returns False."""
        hashed = hash_password("SomePassword123!")
        assert verify_password("", hashed) is False
        assert verify_password("test", "") is False

    def test_hash_password_empty_raises(self):
        """Empty password raises ValueError."""
        with pytest.raises(ValueError):
            hash_password("")

    def test_needs_rehash_current_rounds(self):
        """Hash with current rounds doesn't need rehash."""
        hashed = hash_password("TestPassword123!")
        assert needs_rehash(hashed) is False

    def test_needs_rehash_invalid_hash(self):
        """Invalid hash format returns True for rehash."""
        assert needs_rehash("invalid") is True
        assert needs_rehash("") is True


# ============================================================================
# PASSWORD VALIDATION TESTS
# ============================================================================


class TestPasswordValidation:
    """Tests for password validation."""

    def test_valid_password(self):
        """Valid password passes all checks."""
        result = validate_password(
            "SecureP@ssw0rd123",
            HIPAA_PASSWORD_REQUIREMENTS,
        )
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_password_too_short(self):
        """Short password fails validation."""
        result = validate_password("Short1!", HIPAA_PASSWORD_REQUIREMENTS)
        assert result.is_valid is False
        assert any("at least 12" in e for e in result.errors)

    def test_password_missing_uppercase(self):
        """Password without uppercase fails."""
        result = validate_password(
            "lowercase123!@#",
            HIPAA_PASSWORD_REQUIREMENTS,
        )
        assert result.is_valid is False
        assert any("uppercase" in e.lower() for e in result.errors)

    def test_password_missing_lowercase(self):
        """Password without lowercase fails."""
        result = validate_password(
            "UPPERCASE123!@#",
            HIPAA_PASSWORD_REQUIREMENTS,
        )
        assert result.is_valid is False
        assert any("lowercase" in e.lower() for e in result.errors)

    def test_password_missing_numbers(self):
        """Password without numbers fails."""
        result = validate_password(
            "NoNumbers!@#abc",
            HIPAA_PASSWORD_REQUIREMENTS,
        )
        assert result.is_valid is False
        assert any("number" in e.lower() for e in result.errors)

    def test_password_missing_special(self):
        """Password without special chars fails."""
        result = validate_password(
            "NoSpecialChars123",
            HIPAA_PASSWORD_REQUIREMENTS,
        )
        assert result.is_valid is False
        assert any("special" in e.lower() for e in result.errors)

    def test_common_password_rejected(self):
        """Common passwords are rejected."""
        result = validate_password(
            "password123!AB",
            HIPAA_PASSWORD_REQUIREMENTS,
        )
        assert result.is_valid is False
        assert any("common" in e.lower() for e in result.errors)

    def test_password_with_email(self):
        """Password containing email parts fails."""
        result = validate_password(
            "JohnDoe123!@#ab",
            HIPAA_PASSWORD_REQUIREMENTS,
            user_email="john.doe@example.com",
        )
        assert result.is_valid is False

    def test_password_strength_weak(self):
        """Weak password gets low score."""
        result = validate_password(
            "abc",
            PasswordRequirements(
                min_length=3,
                require_uppercase=False,
                require_lowercase=False,
                require_numbers=False,
                require_special_chars=False,
                prevent_common_passwords=False,
                prevent_user_info_in_password=False,
            ),
        )
        assert result.strength in ("weak", "fair")

    def test_password_strength_strong(self):
        """Strong password gets high score."""
        result = validate_password(
            "VerySecure@Password123!XYZ",
            HIPAA_PASSWORD_REQUIREMENTS,
        )
        assert result.strength in ("strong", "very_strong")


# ============================================================================
# TOKEN GENERATION TESTS
# ============================================================================


class TestTokenGeneration:
    """Tests for secure token generation."""

    def test_reset_token_length(self):
        """Reset token has correct length."""
        token = generate_reset_token(64)
        assert len(token) > 80  # Base64 encoding increases length

    def test_reset_token_unique(self):
        """Reset tokens are unique."""
        tokens = [generate_reset_token() for _ in range(100)]
        assert len(set(tokens)) == 100

    def test_temporary_password_meets_requirements(self):
        """Temporary password meets security requirements."""
        password = generate_temporary_password(16)
        assert len(password) == 16
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*()_+-=" for c in password)

    def test_backup_codes_format(self):
        """Backup codes have correct format."""
        codes = generate_backup_codes(count=10, length=8)
        assert len(codes) == 10
        for code in codes:
            assert "-" in code
            assert len(code.replace("-", "")) == 8


# ============================================================================
# JWT TOKEN TESTS
# ============================================================================


class TestJWTTokens:
    """Tests for JWT token operations."""

    @pytest.fixture
    def user_data(self):
        return {
            "user_id": "550e8400-e29b-41d4-a716-446655440001",
            "email": "doctor@neuraxis.health",
            "role": "doctor",
            "organization_id": "550e8400-e29b-41d4-a716-446655440000",
            "permissions": ["patient:read", "diagnosis:read"],
            "session_id": "session-123456",
        }

    def test_create_access_token(self, user_data):
        """Access token is created successfully."""
        token = create_access_token(**user_data)
        assert isinstance(token, str)
        assert len(token) > 100

    def test_verify_access_token(self, user_data):
        """Access token verifies correctly."""
        token = create_access_token(**user_data)
        payload = verify_access_token(token)

        assert payload.sub == user_data["user_id"]
        assert payload.email == user_data["email"]
        assert payload.role == user_data["role"]
        assert payload.type == "access"

    def test_create_refresh_token(self, user_data):
        """Refresh token is created successfully."""
        token = create_refresh_token(
            user_id=user_data["user_id"],
            session_id=user_data["session_id"],
        )
        assert isinstance(token, str)

    def test_verify_refresh_token(self, user_data):
        """Refresh token verifies correctly."""
        token = create_refresh_token(
            user_id=user_data["user_id"],
            session_id=user_data["session_id"],
        )
        payload = verify_refresh_token(token)

        assert payload.sub == user_data["user_id"]
        assert payload.session_id == user_data["session_id"]
        assert payload.type == "refresh"

    def test_token_pair_creation(self, user_data):
        """Token pair contains both tokens and expiry."""
        access, refresh, expires_in = create_token_pair(**user_data)

        assert isinstance(access, str)
        assert isinstance(refresh, str)
        assert expires_in == 15 * 60  # 15 minutes in seconds

    def test_password_reset_token(self, user_data):
        """Password reset token works correctly."""
        token = create_password_reset_token(
            user_id=user_data["user_id"],
            email=user_data["email"],
        )
        payload = verify_password_reset_token(token)

        assert payload.sub == user_data["user_id"]
        assert payload.email == user_data["email"]
        assert payload.type == "reset_password"

    def test_invalid_token_raises(self):
        """Invalid token raises TokenInvalidError."""
        with pytest.raises(TokenInvalidError):
            verify_access_token("invalid.token.here")

    def test_wrong_token_type_raises(self, user_data):
        """Wrong token type raises error."""
        refresh_token = create_refresh_token(
            user_id=user_data["user_id"],
            session_id=user_data["session_id"],
        )
        with pytest.raises(TokenInvalidError):
            verify_access_token(refresh_token)  # Using refresh as access

    def test_token_not_expired(self, user_data):
        """Fresh token is not expired."""
        token = create_access_token(**user_data)
        assert is_token_expired(token) is False

    def test_token_remaining_time(self, user_data):
        """Token remaining time is calculated correctly."""
        token = create_access_token(**user_data)
        remaining = get_token_remaining_time(token)

        # Should be close to 15 minutes (900 seconds)
        assert 850 < remaining < 910


# ============================================================================
# ENTROPY & CRACK TIME TESTS
# ============================================================================


class TestPasswordAnalysis:
    """Tests for password analysis functions."""

    def test_entropy_calculation(self):
        """Entropy increases with complexity."""
        simple = calculate_password_entropy("password")
        complex = calculate_password_entropy("P@ssw0rd123!")

        assert complex > simple

    def test_crack_time_weak(self):
        """Weak password shows quick crack time."""
        result = estimate_crack_time("abc")
        assert result in ("instantly", "seconds", "minutes")

    def test_crack_time_strong(self):
        """Strong password shows long crack time."""
        result = estimate_crack_time("VerySecure@Password123!XYZ789")
        assert "years" in result or "centuries" in result.lower()


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
