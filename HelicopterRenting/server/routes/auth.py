import uuid
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr

from server import config
from server.auth.dependencies import SESSION_COOKIE, get_current_user
from server.auth.security import (
    generate_session_token,
    hash_password,
    session_expiry,
    verify_password,
)
from server.db.pool import get_connection

router = APIRouter()


class SignUpBody(BaseModel):
    name: str
    email: EmailStr
    password: str


class SignInBody(BaseModel):
    email: EmailStr
    password: str


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=config.IS_PRODUCTION,
        max_age=int(60 * 60 * 24 * 30),
        path="/",
    )


@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
def sign_up(body: SignUpBody, response: Response):
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (body.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="An account with that email already exists")

        user_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO users (id, name, email, password_hash) VALUES (%s, %s, %s, %s)",
            (user_id, body.name, body.email, hash_password(body.password)),
        )

        token = generate_session_token()
        cursor.execute(
            "INSERT INTO sessions (id, user_id, token, expires_at) VALUES (%s, %s, %s, %s)",
            (str(uuid.uuid4()), user_id, token, session_expiry()),
        )
        conn.commit()
    finally:
        conn.close()

    _set_session_cookie(response, token)
    return {"id": user_id, "name": body.name, "email": body.email}


@router.post("/sign-in")
def sign_in(body: SignInBody, response: Response):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (body.email,))
        user = cursor.fetchone()
        if not user or not verify_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = generate_session_token()
        cursor.execute(
            "INSERT INTO sessions (id, user_id, token, expires_at) VALUES (%s, %s, %s, %s)",
            (str(uuid.uuid4()), user["id"], token, session_expiry()),
        )
        conn.commit()
    finally:
        conn.close()

    _set_session_cookie(response, token)
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


@router.post("/sign-out")
def sign_out(response: Response, session_token: Optional[str] = Cookie(default=None)):
    if session_token:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = %s", (session_token,))
            conn.commit()
        finally:
            conn.close()
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/session")
def session(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not signed in")
    return user
