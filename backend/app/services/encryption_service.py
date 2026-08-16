from cryptography.fernet import Fernet
from typing import Optional
from app.core.config import settings

class EncryptionService:
    """Symmetric encryption service for database columns at-rest (using Fernet)."""

    def __init__(self):
        key = settings.DB_ENCRYPTION_KEY
        if not key or key == "placeholder":
            # Fallback stable key for testing/dev so values are decryptable across restarts
            key = "T1Boc2QzSDRlNTZkNzhqOWowMTIzNDU2NzhqOWowMTI="
        self.fernet = Fernet(key.encode())

    def encrypt(self, plain_text: Optional[str]) -> Optional[str]:
        """Encrypt plain text to cypher text."""
        if plain_text is None or not isinstance(plain_text, str):
            return plain_text
        return self.fernet.encrypt(plain_text.encode()).decode()

    def decrypt(self, cipher_text: Optional[str]) -> Optional[str]:
        """Decrypt cypher text back to plain text, failing gracefully to original text if not encrypted."""
        if cipher_text is None or not isinstance(cipher_text, str):
            return cipher_text
        try:
            return self.fernet.decrypt(cipher_text.encode()).decode()
        except Exception:
            # Fallback if text is not encrypted (e.g. legacy data)
            return cipher_text

encryption_service = EncryptionService()


from sqlalchemy.types import TypeDecorator, String

class EncryptedString(TypeDecorator):
    """Custom SQLAlchemy type for transparent column encryption at-rest."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return encryption_service.encrypt(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return encryption_service.decrypt(value)

