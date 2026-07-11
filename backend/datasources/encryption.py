import json
from django.conf import settings
from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    key = settings.DATASOURCE_ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_config(config: dict) -> str:
    """Encrypt connection_config dict to a Fernet token string."""
    if not config:
        return ""
    return _get_fernet().encrypt(json.dumps(config).encode()).decode()


def decrypt_config(token: str) -> dict:
    """Decrypt Fernet token back to dict."""
    if not token:
        return {}
    try:
        return json.loads(_get_fernet().decrypt(token.encode()))
    except Exception:
        return {}


# Aliases used by tests and other modules
encrypt_connection_config = encrypt_config
decrypt_connection_config = decrypt_config
