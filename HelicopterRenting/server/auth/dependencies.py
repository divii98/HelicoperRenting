from typing import Optional

from fastapi import Cookie, HTTPException, status

from server.db.pool import get_connection

SESSION_COOKIE = "session_token"


def _load_session_user(token: Optional[str]):
    if not token:
        return None
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT u.id, u.name, u.email
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = %s AND s.expires_at > UTC_TIMESTAMP()
            """,
            (token,),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def get_current_user(session_token: Optional[str] = Cookie(default=None)):
    """FastAPI dependency: returns the signed-in user dict, or None."""
    return _load_session_user(session_token)


def require_user(session_token: Optional[str] = Cookie(default=None)):
    """FastAPI dependency: 401s if there is no valid session."""
    user = _load_session_user(session_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be signed in",
        )
    return user
