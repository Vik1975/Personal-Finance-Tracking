"""Tests for transaction endpoints."""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Transaction, Category


@pytest.fixture
async def test_transaction(db_session: AsyncSession, test_user: User) -> Transaction:
    """Create a test transaction."""
    transaction = Transaction(
        user_id=test_user.id,
        date=date.today(),
        amount=Decimal("100.50"),
        currency="USD",
        merchant="Test Store",
        description="Test purchase",
        is_expense=True,
    )
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    return transaction


class TestCreateTransaction:
    """Test transaction creation."""

    async def test_create_transaction_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test creating a transaction."""
        response = await async_client.post(
            "/transactions",
            headers=auth_headers,
            json={
                "date": "2025-12-11",
                "amount": 50.99,
                "currency": "USD",
                "merchant": "Coffee Shop",
                "description": "Morning coffee",
                "is_expense": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == "50.99"
        assert data["merchant"] == "Coffee Shop"
        assert data["currency"] == "USD"
        assert "id" in data

    async def test_create_transaction_without_auth(self, async_client: AsyncClient):
        """Test creating transaction without authentication."""
        response = await async_client.post(
            "/transactions",
            json={
                "date": "2025-12-11",
                "amount": 50.99,
                "currency": "USD",
                "is_expense": True,
            },
        )
        assert response.status_code == 401

    async def test_create_transaction_invalid_amount(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test creating transaction with invalid amount."""
        response = await async_client.post(
            "/transactions",
            headers=auth_headers,
            json={
                "date": "2025-12-11",
                "amount": -50.0,  # Negative amount
                "currency": "USD",
                "is_expense": True,
            },
        )
        assert response.status_code == 422  # Validation error

    async def test_create_transaction_with_category(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_categories: list,
    ):
        """Test creating transaction with category."""
        category = test_categories[0]
        response = await async_client.post(
            "/transactions",
            headers=auth_headers,
            json={
                "date": "2025-12-11",
                "amount": 25.50,
                "currency": "USD",
                "category_id": category.id,
                "merchant": "Restaurant",
                "is_expense": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] == category.id


class TestListTransactions:
    """Test listing transactions."""

    async def test_list_transactions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_transaction: Transaction,
    ):
        """Test listing user's transactions."""
        response = await async_client.get("/transactions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id"] == test_transaction.id

    async def test_list_transactions_without_auth(self, async_client: AsyncClient):
        """Test listing transactions without authentication."""
        response = await async_client.get("/transactions")
        assert response.status_code == 401

    async def test_list_transactions_user_isolation(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_transaction: Transaction,
        test_superuser: User,
        db_session: AsyncSession,
    ):
        """Test that users only see their own transactions."""
        # Create transaction for another user
        other_transaction = Transaction(
            user_id=test_superuser.id,
            date=date.today(),
            amount=Decimal("200.00"),
            currency="USD",
            merchant="Other Store",
            is_expense=True,
        )
        db_session.add(other_transaction)
        await db_session.commit()

        # Test user should only see their own transaction
        response = await async_client.get("/transactions", headers=auth_headers)
        data = response.json()
        transaction_ids = [t["id"] for t in data]
        assert test_transaction.id in transaction_ids
        assert other_transaction.id not in transaction_ids

    async def test_list_transactions_with_filters(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Test listing transactions with filters."""
        # Create transactions with different dates
        t1 = Transaction(
            user_id=test_user.id,
            date=date.today() - timedelta(days=5),
            amount=Decimal("50.00"),
            currency="USD",
            merchant="Store A",
            is_expense=True,
        )
        t2 = Transaction(
            user_id=test_user.id,
            date=date.today(),
            amount=Decimal("100.00"),
            currency="USD",
            merchant="Store B",
            is_expense=True,
        )
        db_session.add_all([t1, t2])
        await db_session.commit()

        # Filter by date
        response = await async_client.get(
            f"/transactions?date_from={date.today().isoformat()}",
            headers=auth_headers,
        )
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == t2.id

    async def test_list_transactions_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Test transaction pagination."""
        # Create multiple transactions
        for i in range(5):
            transaction = Transaction(
                user_id=test_user.id,
                date=date.today(),
                amount=Decimal(f"{i + 1}0.00"),
                currency="USD",
                is_expense=True,
            )
            db_session.add(transaction)
        await db_session.commit()

        # Get with limit
        response = await async_client.get("/transactions?limit=3", headers=auth_headers)
        data = response.json()
        assert len(data) == 3


class TestGetTransaction:
    """Test getting single transaction."""

    async def test_get_transaction_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_transaction: Transaction,
    ):
        """Test getting a transaction by ID."""
        response = await async_client.get(
            f"/transactions/{test_transaction.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_transaction.id
        assert data["amount"] == str(test_transaction.amount)

    async def test_get_nonexistent_transaction(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting non-existent transaction."""
        response = await async_client.get("/transactions/99999", headers=auth_headers)
        assert response.status_code == 404

    async def test_get_other_users_transaction(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_superuser: User,
        db_session: AsyncSession,
    ):
        """Test getting another user's transaction (should fail)."""
        other_transaction = Transaction(
            user_id=test_superuser.id,
            date=date.today(),
            amount=Decimal("200.00"),
            currency="USD",
            is_expense=True,
        )
        db_session.add(other_transaction)
        await db_session.commit()
        await db_session.refresh(other_transaction)

        response = await async_client.get(
            f"/transactions/{other_transaction.id}", headers=auth_headers
        )
        assert response.status_code == 404  # User can't see it


class TestUpdateTransaction:
    """Test updating transactions."""

    async def test_update_transaction_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_transaction: Transaction,
    ):
        """Test updating a transaction."""
        response = await async_client.put(
            f"/transactions/{test_transaction.id}",
            headers=auth_headers,
            json={
                "amount": 150.75,
                "description": "Updated description",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == "150.75"
        assert data["description"] == "Updated description"

    async def test_update_nonexistent_transaction(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test updating non-existent transaction."""
        response = await async_client.put(
            "/transactions/99999",
            headers=auth_headers,
            json={"amount": 100.00},
        )
        assert response.status_code == 404


class TestDeleteTransaction:
    """Test deleting transactions."""

    async def test_delete_transaction_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_transaction: Transaction,
    ):
        """Test deleting a transaction."""
        response = await async_client.delete(
            f"/transactions/{test_transaction.id}", headers=auth_headers
        )
        assert response.status_code == 204

        # Verify it's deleted
        response = await async_client.get(
            f"/transactions/{test_transaction.id}", headers=auth_headers
        )
        assert response.status_code == 404

    async def test_delete_nonexistent_transaction(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent transaction."""
        response = await async_client.delete("/transactions/99999", headers=auth_headers)
        assert response.status_code == 404
