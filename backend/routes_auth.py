"""Create-account and log-in routes for Campus Customs."""

import sqlite3

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field

import auth
from db import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------- Models ----------

class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PublicUser(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: PublicUser


def row_to_user(row: sqlite3.Row) -> PublicUser:
    return PublicUser(
        id=row["id"],
        first_name=row["first_name"] or "",
        last_name=row["last_name"] or "",
        email=row["email"],
    )


# ---------- Routes ----------

@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(req: SignupRequest) -> AuthResponse:
    email = req.email.strip().lower()
    password_hash = auth.hash_password(req.password)
    full_name = f"{req.first_name.strip()} {req.last_name.strip()}"

    with get_db() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="An account with that email already exists.")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) "
            "VALUES (?, ?, ?, ?, ?)",
            (full_name, email, password_hash, req.first_name.strip(), req.last_name.strip()),
        )
        conn.commit()
        user_id = cur.lastrowid
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    return AuthResponse(token=auth.create_token(user_id), user=row_to_user(row))


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest) -> AuthResponse:
    email = req.email.strip().lower()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    # Same generic error whether the email is unknown or the password is wrong,
    # so attackers can't tell which emails are registered.
    if row is None or not auth.verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    # Transparently upgrade legacy seed hashes to our stronger 4-part format
    # now that we have the plaintext in hand and know it's correct.
    if auth.needs_rehash(row["password_hash"]):
        with get_db() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (auth.hash_password(req.password), row["id"]),
            )
            conn.commit()

    return AuthResponse(token=auth.create_token(row["id"]), user=row_to_user(row))


# ---------- Dependency for protected routes (used in later problems) ----------

def get_current_user(authorization: str | None = Header(default=None)) -> PublicUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    token = authorization.split(" ", 1)[1]
    user_id = auth.decode_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Account no longer exists.")
    return row_to_user(row)


def get_optional_user(authorization: str | None = Header(default=None)) -> PublicUser | None:
    """Like get_current_user, but returns None instead of 401 for guests.

    Used by the chat route so guests can chat while logged-in users are recognized.
    """
    if not authorization:
        return None
    try:
        return get_current_user(authorization)
    except HTTPException:
        return None


@router.get("/me", response_model=PublicUser)
def me(user: PublicUser = Depends(get_current_user)) -> PublicUser:
    return user
