"""Tests for security utilities."""

import pytest
from datetime import timedelta
from app.core.security import verify_password, get_password_hash, create_access_token


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_and_verify_password(self):
        """Test hashing and verifying a password."""
        password = "mysecurepassword123"
        hashed = get_password_hash(password)

        # Hash should be different from original
        assert hashed != password

        # Verification should succeed
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test verifying incorrect password."""
        password = "correctpassword"
        hashed = get_password_hash(password)

        # Wrong password should fail verification
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different (different salts)
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation."""

    def test_create_access_token(self):
        """Test creating JWT access token."""
        data = {"sub": "user@example.com"}
        token = create_access_token(data)

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_with_custom_expiry(self):
        """Test creating token with custom expiration."""
        data = {"sub": "user@example.com"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta)

        # Should create valid token
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_subject(self):
        """Test that token encodes the subject."""
        import jwt
        from app.core.config import settings

        email = "test@example.com"
        token = create_access_token({"sub": email})

        # Decode and verify
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == email

    def test_token_has_expiration(self):
        """Test that token has expiration time."""
        import jwt
        from app.core.config import settings

        token = create_access_token({"sub": "user@example.com"})

        # Decode and check expiration
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload
        assert isinstance(payload["exp"], int)
