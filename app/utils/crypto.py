from cryptography.fernet import Fernet, InvalidToken
from app.config import settings

_cached: Fernet | None = None

def get_fernet() -> Fernet:
	global _cached
	if _cached is None:
		if not settings.app_encryption_key:
			raise RuntimeError("APP_ENCRYPTION_KEY is required")
		_cached = Fernet(settings.app_encryption_key)
	return _cached

def encrypt_text(plain: str) -> str:
	return get_fernet().encrypt(plain.encode()).decode()

def decrypt_text(token: str) -> str:
	return get_fernet().decrypt(token.encode()).decode()