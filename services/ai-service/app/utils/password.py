"""
NEURAXIS - Password Hashing & Validation Utilities
===================================================
Secure password handling with bcrypt hashing and comprehensive validation.
HIPAA-compliant password policies for healthcare applications.
"""

import re
import secrets
import string
from dataclasses import dataclass
from typing import Optional

import bcrypt

# ============================================================================
# PASSWORD VALIDATION
# ============================================================================

# Common passwords to prevent (top 100 most common)
COMMON_PASSWORDS = {
    "password",
    "123456",
    "12345678",
    "qwerty",
    "abc123",
    "monkey",
    "1234567",
    "letmein",
    "trustno1",
    "dragon",
    "baseball",
    "iloveyou",
    "master",
    "sunshine",
    "ashley",
    "bailey",
    "passw0rd",
    "shadow",
    "123123",
    "654321",
    "superman",
    "qazwsx",
    "michael",
    "football",
    "password1",
    "password123",
    "welcome",
    "jesus",
    "ninja",
    "mustang",
    "password1!",
    "admin",
    "admin123",
    "root",
    "toor",
    "pass",
    "test",
    "guest",
    "master",
    "changeme",
    "passwd",
    "login",
}


@dataclass
class PasswordRequirements:
    """Password policy requirements."""

    min_length: int = 12
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    prevent_common_passwords: bool = True
    prevent_user_info_in_password: bool = True


@dataclass
class PasswordValidationResult:
    """Result of password validation."""

    is_valid: bool
    errors: list[str]
    strength: str  # weak, fair, good, strong, very_strong
    score: int  # 0-100


# Default requirements for healthcare (HIPAA-compliant)
HIPAA_PASSWORD_REQUIREMENTS = PasswordRequirements(
    min_length=12,
    max_length=128,
    require_uppercase=True,
    require_lowercase=True,
    require_numbers=True,
    require_special_chars=True,
    prevent_common_passwords=True,
    prevent_user_info_in_password=True,
)


def validate_password(
    password: str,
    requirements: PasswordRequirements = HIPAA_PASSWORD_REQUIREMENTS,
    user_email: Optional[str] = None,
    user_first_name: Optional[str] = None,
    user_last_name: Optional[str] = None,
) -> PasswordValidationResult:
    """
    Validate password against security requirements.

    Args:
        password: The password to validate
        requirements: Password requirements to check against
        user_email: User's email to prevent in password
        user_first_name: User's first name to prevent in password
        user_last_name: User's last name to prevent in password

    Returns:
        PasswordValidationResult with validation status and details
    """
    errors: list[str] = []
    score = 0

    # Length checks
    if len(password) < requirements.min_length:
        errors.append(f"Password must be at least {requirements.min_length} characters long")
    else:
        score += 20

    if len(password) > requirements.max_length:
        errors.append(f"Password must be at most {requirements.max_length} characters long")

    # Character type checks
    if requirements.require_uppercase and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    elif re.search(r"[A-Z]", password):
        score += 15

    if requirements.require_lowercase and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    elif re.search(r"[a-z]", password):
        score += 15

    if requirements.require_numbers and not re.search(r"\d", password):
        errors.append("Password must contain at least one number")
    elif re.search(r"\d", password):
        score += 15

    if requirements.require_special_chars and not re.search(
        r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password
    ):
        errors.append("Password must contain at least one special character")
    elif re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        score += 15

    # Common password check
    if requirements.prevent_common_passwords:
        if password.lower() in COMMON_PASSWORDS:
            errors.append("Password is too common and easily guessable")
            score -= 30
        else:
            score += 10

    # User info in password check
    if requirements.prevent_user_info_in_password:
        password_lower = password.lower()

        if user_email:
            email_parts = user_email.lower().split("@")[0].split(".")
            for part in email_parts:
                if len(part) > 2 and part in password_lower:
                    errors.append("Password cannot contain parts of your email address")
                    break

        if user_first_name and len(user_first_name) > 2:
            if user_first_name.lower() in password_lower:
                errors.append("Password cannot contain your first name")

        if user_last_name and len(user_last_name) > 2:
            if user_last_name.lower() in password_lower:
                errors.append("Password cannot contain your last name")

    # Bonus for length
    if len(password) >= 16:
        score += 10
    if len(password) >= 20:
        score += 10

    # Ensure score is within bounds
    score = max(0, min(100, score))

    # Determine strength
    if score < 30:
        strength = "weak"
    elif score < 50:
        strength = "fair"
    elif score < 70:
        strength = "good"
    elif score < 90:
        strength = "strong"
    else:
        strength = "very_strong"

    return PasswordValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        strength=strength,
        score=score,
    )


# ============================================================================
# PASSWORD HASHING
# ============================================================================

# bcrypt work factor (2^12 = 4096 iterations)
# Higher = more secure but slower. 12 is recommended for 2024+
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string

    Raises:
        ValueError: If password is empty
    """
    if not password:
        raise ValueError("Password cannot be empty")

    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password to verify
        password_hash: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    if not password or not password_hash:
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Invalid hash format
        return False


def needs_rehash(password_hash: str) -> bool:
    """
    Check if a password hash needs to be rehashed (e.g., work factor increased).

    Args:
        password_hash: Current password hash

    Returns:
        True if password should be rehashed with new settings
    """
    try:
        # Extract the current rounds from the hash
        # bcrypt hash format: $2b$12$...
        parts = password_hash.split("$")
        if len(parts) >= 3:
            current_rounds = int(parts[2])
            return current_rounds < BCRYPT_ROUNDS
        return True
    except (ValueError, IndexError):
        return True


# ============================================================================
# SECURE TOKEN GENERATION
# ============================================================================


def generate_reset_token(length: int = 64) -> str:
    """
    Generate a cryptographically secure password reset token.

    Args:
        length: Length of the token in characters

    Returns:
        URL-safe random token string
    """
    return secrets.token_urlsafe(length)


def generate_temporary_password(length: int = 16) -> str:
    """
    Generate a secure temporary password.

    Args:
        length: Length of the temporary password

    Returns:
        Random password that meets requirements
    """
    # Ensure we have at least one of each required character type
    password_chars = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*()_+-="),
    ]

    # Fill the rest with random characters
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    password_chars.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Shuffle to avoid predictable pattern
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


def generate_backup_codes(count: int = 10, length: int = 8) -> list[str]:
    """
    Generate MFA backup codes.

    Args:
        count: Number of backup codes to generate
        length: Length of each backup code

    Returns:
        List of backup code strings
    """
    codes = []
    for _ in range(count):
        # Format: XXXX-XXXX for readability
        part1 = "".join(
            secrets.choice(string.digits + string.ascii_uppercase) for _ in range(length // 2)
        )
        part2 = "".join(
            secrets.choice(string.digits + string.ascii_uppercase) for _ in range(length // 2)
        )
        codes.append(f"{part1}-{part2}")

    return codes


# ============================================================================
# PASSWORD STRENGTH METER (for frontend feedback)
# ============================================================================


def calculate_password_entropy(password: str) -> float:
    """
    Calculate the entropy (randomness) of a password in bits.

    Args:
        password: Password to analyze

    Returns:
        Entropy in bits
    """
    import math

    # Determine character pool size
    pool_size = 0
    if re.search(r"[a-z]", password):
        pool_size += 26
    if re.search(r"[A-Z]", password):
        pool_size += 26
    if re.search(r"\d", password):
        pool_size += 10
    if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        pool_size += 32

    if pool_size == 0:
        return 0

    # Entropy = length * log2(pool_size)
    entropy = len(password) * math.log2(pool_size)

    return round(entropy, 2)


def estimate_crack_time(password: str) -> str:
    """
    Estimate time to crack a password (for user feedback).

    Args:
        password: Password to analyze

    Returns:
        Human-readable time estimate string
    """
    entropy = calculate_password_entropy(password)

    # Assume 10 billion guesses per second (modern GPU)
    guesses_per_second = 10_000_000_000

    # Average guesses = 2^(entropy-1)
    import math

    if entropy <= 0:
        return "instantly"

    average_guesses = 2 ** (entropy - 1)
    seconds = average_guesses / guesses_per_second

    # Convert to human-readable format
    if seconds < 1:
        return "instantly"
    elif seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours"
    elif seconds < 31536000:
        return f"{int(seconds / 86400)} days"
    elif seconds < 31536000 * 100:
        return f"{int(seconds / 31536000)} years"
    elif seconds < 31536000 * 1000000:
        return f"{int(seconds / 31536000 / 1000)} thousand years"
    else:
        return "millions of years"
