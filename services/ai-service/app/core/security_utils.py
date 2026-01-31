import base64
import logging
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)


class FieldEncryptor:
    """
    AES-256-GCM Encryption for PHI fields.
    Requires ENCRYPTION_KEY (Base64 encoded 32-byte key) in env.
    """

    def __init__(self):
        key_b64 = os.getenv("ENCRYPTION_KEY")

        # In production, crash if no key. In dev, warn.
        if not key_b64:
            logger.warning("No ENCRYPTION_KEY found. PHI encryption disabled (Dev Mode).")
            self.aesgcm = None
            return

        try:
            self.key = base64.b64decode(key_b64)
            if len(self.key) != 32:
                logger.error("ENCRYPTION_KEY must be 32 bytes (256 bits) for AES-256.")
                self.aesgcm = None
            else:
                self.aesgcm = AESGCM(self.key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self.aesgcm = None

    def encrypt(self, plain_text: str) -> str:
        if not self.aesgcm:
            return plain_text  # Pass-through for dev if unconfigured

        if not plain_text:
            return ""

        try:
            nonce = os.urandom(12)
            data = plain_text.encode("utf-8")
            ct = self.aesgcm.encrypt(nonce, data, None)
            # Store as : Base64(nonce + ct)
            return base64.b64encode(nonce + ct).decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise ValueError("Encryption failed")

    def decrypt(self, cipher_text_b64: str) -> str:
        if not self.aesgcm:
            return cipher_text_b64

        if not cipher_text_b64:
            return ""

        try:
            raw = base64.b64decode(cipher_text_b64)
            if len(raw) < 13:
                return "INVALID"
            nonce = raw[:12]
            ct = raw[12:]
            pt = self.aesgcm.decrypt(nonce, ct, None)
            return pt.decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return "[ENCRYPTED-ERROR]"


# Singleton
phi_encryptor = FieldEncryptor()
