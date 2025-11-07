"""Unit tests for security utilities"""

import pytest
from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
    verify_password,
)


def test_create_access_token():
    """Test JWT access token creation"""
    user_id = 123
    token = create_access_token(subject=user_id)

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_expiration():
    """Test access token with custom expiration"""
    user_id = 123
    expires_delta = timedelta(minutes=15)
    token = create_access_token(subject=user_id, expires_delta=expires_delta)

    assert token is not None
    decoded = verify_token(token)
    assert decoded is not None
    assert decoded["sub"] == str(user_id)


def test_create_refresh_token():
    """Test refresh token creation"""
    user_id = 123
    token = create_refresh_token(subject=user_id)

    assert token is not None
    assert isinstance(token, str)

    decoded = verify_token(token)
    assert decoded is not None
    assert decoded["sub"] == str(user_id)
    assert decoded.get("type") == "refresh"


def test_verify_token_valid():
    """Test token verification with valid token"""
    user_id = 123
    token = create_access_token(subject=user_id)
    decoded = verify_token(token)

    assert decoded is not None
    assert decoded["sub"] == str(user_id)
    assert "exp" in decoded


def test_verify_token_invalid():
    """Test token verification with invalid token"""
    invalid_token = "invalid.token.here"
    decoded = verify_token(invalid_token)

    assert decoded is None


def test_password_hashing():
    """Test password hashing"""
    password = "my_secure_password"
    hashed = get_password_hash(password)

    assert hashed is not None
    assert hashed != password
    assert len(hashed) > 0


def test_password_verification():
    """Test password verification"""
    password = "my_secure_password"
    hashed = get_password_hash(password)

    # Correct password should verify
    assert verify_password(password, hashed) is True

    # Wrong password should not verify
    assert verify_password("wrong_password", hashed) is False
