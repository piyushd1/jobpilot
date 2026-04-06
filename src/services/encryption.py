"""PII field encryption for data at rest.

Uses Fernet symmetric encryption (AES-128-CBC) for PII fields
like email, phone, name. Keys managed via environment variable
(production: Vault/K8s Secrets).
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet

from src.utils.logging import get_logger

logger = get_logger(__name__)


class PIIEncryption:
    """Encrypt/decrypt PII fields using Fernet."""

    def __init__(self, key: str | None = None):
        self._key = key or os.environ.get("PII_ENCRYPTION_KEY", "")
        if not self._key:
            self._key = Fernet.generate_key().decode()
            logger.warning("No PII_ENCRYPTION_KEY set, generated ephemeral key")
        if isinstance(self._key, str):
            self._key = self._key.encode()
        self._fernet = Fernet(self._key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string, return base64-encoded ciphertext."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a base64-encoded ciphertext."""
        return self._fernet.decrypt(ciphertext.encode()).decode()

    def encrypt_dict_fields(self, data: dict, fields: list[str]) -> dict:
        """Encrypt specified fields in a dict, in-place."""
        for field in fields:
            if field in data and data[field]:
                data[f"{field}_encrypted"] = self.encrypt(str(data[field]))
                data[field] = "***"
        return data


pii_encryption = PIIEncryption()
