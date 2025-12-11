"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


class TestSignup:
    """Test user registration."""

    async def test_signup_success(self, async_client: AsyncClient):
        """Test successful user registration."""
        response = await async_client.post(
            "/auth/signup",
            json={
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "newpassword123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "id" in data
        assert "created_at" in data

    async def test_signup_duplicate_email(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test signup with existing email."""
        response = await async_client.post(
            "/auth/signup",
            json={
                "email": test_user.email,
                "full_name": "Another User",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_signup_invalid_email(self, async_client: AsyncClient):
        """Test signup with invalid email format."""
        response = await async_client.post(
            "/auth/signup",
            json={
                "email": "not-an-email",
                "full_name": "Test User",
                "password": "password123",
            },
        )
        assert response.status_code == 422  # Validation error

    async def test_signup_short_password(self, async_client: AsyncClient):
        """Test signup with password too short."""
        response = await async_client.post(
            "/auth/signup",
            json={
                "email": "user@example.com",
                "full_name": "Test User",
                "password": "short",
            },
        )
        assert response.status_code == 422  # Validation error

    async def test_signup_missing_fields(self, async_client: AsyncClient):
        """Test signup with missing required fields."""
        response = await async_client.post(
            "/auth/signup",
            json={"email": "user@example.com"},
        )
        assert response.status_code == 422


class TestLogin:
    """Test user login."""

    async def test_login_success(self, async_client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await async_client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    async def test_login_wrong_password(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test login with incorrect password."""
        response = await async_client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Test login with non-existent user."""
        response = await async_client.post(
            "/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401

    async def test_login_inactive_user(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test login with inactive user."""
        from app.core.security import get_password_hash

        inactive_user = User(
            email="inactive@example.com",
            full_name="Inactive User",
            hashed_password=get_password_hash("password123"),
            is_active=False,
        )
        db_session.add(inactive_user)
        await db_session.commit()

        response = await async_client.post(
            "/auth/login",
            data={
                "username": "inactive@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()


class TestGetCurrentUser:
    """Test getting current user profile."""

    async def test_get_me_success(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test getting current user profile."""
        response = await async_client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["id"] == test_user.id

    async def test_get_me_no_token(self, async_client: AsyncClient):
        """Test getting profile without authentication."""
        response = await async_client.get("/auth/me")
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    async def test_get_me_invalid_token(self, async_client: AsyncClient):
        """Test getting profile with invalid token."""
        response = await async_client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower()

    async def test_get_me_malformed_header(self, async_client: AsyncClient):
        """Test getting profile with malformed auth header."""
        response = await async_client.get(
            "/auth/me", headers={"Authorization": "InvalidFormat"}
        )
        assert response.status_code == 401


class TestTokenSecurity:
    """Test token security features."""

    async def test_token_contains_user_email(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test that token contains user identifier."""
        response = await async_client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123",
            },
        )
        token = response.json()["access_token"]

        # Decode token (without verification for testing)
        import jwt

        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == test_user.email
        assert "exp" in payload  # Has expiration

    async def test_different_users_different_tokens(
        self, async_client: AsyncClient, test_user: User, test_superuser: User
    ):
        """Test that different users get different tokens."""
        response1 = await async_client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
        )
        token1 = response1.json()["access_token"]

        response2 = await async_client.post(
            "/auth/login",
            data={"username": test_superuser.email, "password": "adminpassword123"},
        )
        token2 = response2.json()["access_token"]

        assert token1 != token2
