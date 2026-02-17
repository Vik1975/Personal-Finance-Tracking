"""Tests for accounts API endpoints."""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Account


@pytest.mark.asyncio
class TestCreateAccount:
    """Test account creation."""

    async def test_create_account_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test successful account creation."""
        response = await async_client.post(
            "/accounts",
            json={
                "name": "Savings Account",
                "account_type": "savings",
                "currency": "USD",
                "balance": 1000.00,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Savings Account"
        assert data["account_type"] == "savings"
        assert data["currency"] == "USD"
        assert float(data["balance"]) == 1000.00

    async def test_create_account_without_auth(self, async_client: AsyncClient):
        """Test account creation without authentication."""
        response = await async_client.post(
            "/accounts",
            json={"name": "Test Account", "account_type": "checking", "currency": "USD"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestListAccounts:
    """Test listing accounts."""

    async def test_list_accounts(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test listing user's accounts."""
        # Create test accounts
        accounts = [
            Account(name="Checking", account_type="checking", currency="USD", balance=Decimal("500"), user_id=test_user.id),
            Account(name="Savings", account_type="savings", currency="USD", balance=Decimal("2000"), user_id=test_user.id),
        ]
        for acc in accounts:
            db_session.add(acc)
        await db_session.commit()

        response = await async_client.get("/accounts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    async def test_list_accounts_without_auth(self, async_client: AsyncClient):
        """Test listing accounts without authentication."""
        response = await async_client.get("/accounts")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetAccount:
    """Test getting single account."""

    async def test_get_account_success(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test getting account by ID."""
        account = Account(name="Test Account", account_type="checking", currency="USD", balance=Decimal("1000"), user_id=test_user.id)
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)

        response = await async_client.get(f"/accounts/{account.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account.id
        assert data["name"] == "Test Account"

    async def test_get_nonexistent_account(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting non-existent account."""
        response = await async_client.get("/accounts/99999", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateAccount:
    """Test updating account."""

    async def test_update_account_success(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test updating account."""
        account = Account(name="Old Name", account_type="checking", currency="USD", balance=Decimal("1000"), user_id=test_user.id)
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)

        response = await async_client.put(
            f"/accounts/{account.id}",
            json={"name": "New Name", "account_type": "savings", "currency": "EUR", "balance": 2000.00},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["account_type"] == "savings"


@pytest.mark.asyncio
class TestDeleteAccount:
    """Test deleting account."""

    async def test_delete_account_success(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test soft deleting account."""
        account = Account(name="To Delete", account_type="checking", currency="USD", balance=Decimal("100"), user_id=test_user.id)
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)

        response = await async_client.delete(f"/accounts/{account.id}", headers=auth_headers)
        assert response.status_code == 204
