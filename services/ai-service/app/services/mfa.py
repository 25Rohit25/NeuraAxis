"""
NEURAXIS - Multi-Factor Authentication Service
===============================================
TOTP-based MFA implementation with backup codes.
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote

from cryptography.fernet import Fernet

from app.core.config import get_settings

settings = get_settings()

# TOTP Configuration
TOTP_DIGITS = 6
TOTP_INTERVAL = 30
TOTP_WINDOW = 1
TOTP_SECRET_LENGTH = 20
ISSUER_NAME = "NEURAXIS"
BACKUP_CODE_COUNT = 10
BACKUP_CODE_LENGTH = 8


@dataclass
class MFASetupData:
    """Data returned when setting up MFA."""

    secret: str
    secret_encrypted: bytes
    qr_code_url: str
    provisioning_uri: str
    backup_codes: list[str]
    backup_codes_hashed: list[str]


@dataclass
class MFAVerificationResult:
    """Result of MFA verification."""

    success: bool
    message: str
    used_backup_code: bool = False
    backup_code_index: Optional[int] = None


def _get_encryption_key() -> bytes:
    key = hashlib.sha256(settings.mfa_encryption_key.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_secret(secret: str) -> bytes:
    fernet = Fernet(_get_encryption_key())
    return fernet.encrypt(secret.encode())


def decrypt_secret(encrypted_secret: bytes) -> str:
    fernet = Fernet(_get_encryption_key())
    return fernet.decrypt(encrypted_secret).decode()


def generate_secret() -> str:
    random_bytes = secrets.token_bytes(TOTP_SECRET_LENGTH)
    return base64.b32encode(random_bytes).decode("utf-8").rstrip("=")


def _hotp(secret: str, counter: int) -> str:
    secret_padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(secret_padded.upper())
    counter_bytes = struct.pack(">Q", counter)
    hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    offset = hmac_hash[-1] & 0x0F
    truncated = struct.unpack(">I", hmac_hash[offset : offset + 4])[0] & 0x7FFFFFFF
    code = truncated % (10**TOTP_DIGITS)
    return str(code).zfill(TOTP_DIGITS)


def generate_totp(secret: str, timestamp: Optional[float] = None) -> str:
    if timestamp is None:
        timestamp = time.time()
    counter = int(timestamp // TOTP_INTERVAL)
    return _hotp(secret, counter)


def verify_totp(secret: str, code: str, window: int = TOTP_WINDOW) -> bool:
    if not code or len(code) != TOTP_DIGITS:
        return False
    counter = int(time.time() // TOTP_INTERVAL)
    for offset in range(-window, window + 1):
        if hmac.compare_digest(code, _hotp(secret, counter + offset)):
            return True
    return False


def generate_provisioning_uri(secret: str, email: str) -> str:
    label = f"{ISSUER_NAME}:{email}"
    params = f"secret={secret}&issuer={ISSUER_NAME}&digits={TOTP_DIGITS}&period={TOTP_INTERVAL}"
    return f"otpauth://totp/{quote(label)}?{params}"


def generate_qr_code_url(provisioning_uri: str) -> str:
    return f"https://chart.googleapis.com/chart?cht=qr&chs=200x200&chl={quote(provisioning_uri, safe='')}"


def generate_backup_codes() -> tuple[list[str], list[str]]:
    import string

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    plain_codes, hashed_codes = [], []
    for _ in range(BACKUP_CODE_COUNT):
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        code = f"{code[:4]}-{code[4:]}"
        plain_codes.append(code)
        hashed_codes.append(hashlib.sha256(code.encode()).hexdigest())
    return plain_codes, hashed_codes


def verify_backup_code(code: str, hashed_codes: list[str]) -> tuple[bool, Optional[int]]:
    normalized = code.replace(" ", "").replace("-", "").upper()
    if len(normalized) == 8:
        normalized = f"{normalized[:4]}-{normalized[4:]}"
    code_hash = hashlib.sha256(normalized.encode()).hexdigest()
    for idx, stored in enumerate(hashed_codes):
        if hmac.compare_digest(code_hash, stored):
            return True, idx
    return False, None


def setup_mfa(email: str) -> MFASetupData:
    secret = generate_secret()
    uri = generate_provisioning_uri(secret, email)
    plain, hashed = generate_backup_codes()
    return MFASetupData(
        secret=secret,
        secret_encrypted=encrypt_secret(secret),
        qr_code_url=generate_qr_code_url(uri),
        provisioning_uri=uri,
        backup_codes=plain,
        backup_codes_hashed=hashed,
    )


def verify_mfa_code(
    code: str, encrypted_secret: bytes, backup_codes: Optional[list[str]] = None
) -> MFAVerificationResult:
    normalized = code.strip().replace(" ", "")
    if len(normalized) == 6 and normalized.isdigit():
        if verify_totp(decrypt_secret(encrypted_secret), normalized):
            return MFAVerificationResult(success=True, message="TOTP verified")
    if backup_codes and len(normalized.replace("-", "")) == 8:
        valid, idx = verify_backup_code(normalized, backup_codes)
        if valid:
            return MFAVerificationResult(
                success=True,
                message="Backup code used",
                used_backup_code=True,
                backup_code_index=idx,
            )
    return MFAVerificationResult(success=False, message="Invalid code")
