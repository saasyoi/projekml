import time

import jwt
import pytest

from api.auth import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
    JWT_ALGORITHM,
)


def test_hash_password_is_not_plaintext():
    hashed = hash_password("mysecret123")
    assert hashed != "mysecret123"
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


def test_verify_password_correct():
    hashed = hash_password("mysecret123")
    assert verify_password("mysecret123", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mysecret123")
    assert verify_password("wrongpassword", hashed) is False


def test_verify_password_handles_garbage_hash():
    assert verify_password("anything", "not-a-real-bcrypt-hash") is False


def test_access_token_roundtrip():
    token = create_access_token(user_id=42)
    assert decode_access_token(token) == 42


def test_access_token_expired():
    from api import auth as auth_module
    payload = {"sub": "1", "exp": time.time() - 60}
    expired_token = jwt.encode(payload, auth_module._SECRET_KEY, algorithm=JWT_ALGORITHM)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


def test_access_token_invalid_signature():
    fake_token = jwt.encode({"sub": "1"}, "wrong-key", algorithm=JWT_ALGORITHM)
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(fake_token)
