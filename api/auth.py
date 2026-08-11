import os
import secrets
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import User

logger = logging.getLogger("familysecure_backend")

JWT_ALGORITHM = "HS256"
SESSION_COOKIE_NAME = "fs_session"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))  # 7 days

_SECRET_KEY = os.environ.get("SECRET_KEY")
if not _SECRET_KEY:
    _SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning(
        "SECRET_KEY tidak diset di environment. Menggunakan kunci sementara yang "
        "hanya berlaku selama proses ini berjalan — semua sesi login akan hilang "
        "saat server di-restart. Set SECRET_KEY di .env untuk produksi."
    )

COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").strip().lower() != "false"


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, _SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    payload = jwt.decode(token, _SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return int(payload["sub"])


def set_session_cookie(response: Response, user_id: int) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    # Use set_cookie with max_age=0 instead of delete_cookie — more reliable
    # because it mirrors exactly the same attributes used when the cookie was set,
    # so the browser is guaranteed to recognise and remove it.
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value="",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=0,
        expires=0,
        path="/",
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Sesi tidak ditemukan. Silakan masuk terlebih dahulu.")
    try:
        user_id = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesi telah berakhir. Silakan masuk kembali.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Sesi tidak valid. Silakan masuk kembali.")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Akun tidak ditemukan. Silakan masuk kembali.")
    return user
