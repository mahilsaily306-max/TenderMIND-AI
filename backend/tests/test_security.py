"""Unit tests for security utilities — no DB required."""
from app.core.security import (
    create_access_token,
    decode_token,
    generate_totp_secret,
    get_password_hash,
    verify_password,
    verify_totp,
)


def test_password_hashing():
    password = "test-password-123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_creation_and_decoding():
    data = {"sub": "1", "role": "owner", "agency_id": 1}
    token = create_access_token(data)
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == "1"
    assert decoded["role"] == "owner"
    assert decoded["agency_id"] == 1


def test_totp():
    secret = generate_totp_secret()
    assert len(secret) > 0
    import pyotp
    totp = pyotp.TOTP(secret)
    valid_token = totp.now()
    assert verify_totp(secret, valid_token)
    assert not verify_totp(secret, "000000")
