import secrets
from datetime import datetime, timedelta, timezone

import bcrypt

SESSION_TTL = timedelta(days=30)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_session_token() -> str:
    return secrets.token_hex(32)


def session_expiry() -> datetime:
    return datetime.now(timezone.utc) + SESSION_TTL
