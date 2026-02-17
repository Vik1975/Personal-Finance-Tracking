"""Tests for budgets API endpoints."""

import pytest
from datetime import date
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Budget, Category


@pytest.mark.asyncio
class TestCreateBudget:
    """Test budget creation."""

    async def test_create_budget_success(
        self, async_client: AsyncClient, auth_headers: dict, test_categories: list
    ):
        """Test successful budget creation."""
        response = await async_client.post(
            "/budgets",
            json={
                "name": "Monthly Groceries",
                "amount": 500.00,
                "currency": "USD",
                "period": "monthly",
                "start_date": "2026-02-01",
                "end_date": "2026-02-28",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Monthly Groceries"
        assert float(data["amount"]) == 500.00

    async def test_create_budget_without_auth(self, async_client: AsyncClient):
        """Test budget creation without authentication."""
        response = await async_client.post(
            "/budgets",
            json={"name": "Test Budget", "amount": 100.00, "period": "monthly", "start_date": "2026-02-01"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestListBudgets:
    """Test listing budgets."""

    async def test_list_budgets(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test listing user's budgets."""
        budgets = [
            Budget(
                name="Budget 1",
                amount=Decimal("1000"),
                currency="USD",
                period="monthly",
                start_date=date(2026, 2, 1),
                user_id=test_user.id,
            ),
            Budget(
                name="Budget 2",
                amount=Decimal("500"),
                currency="USD",
                period="weekly",
                start_date=date(2026, 2, 1),
                user_id=test_user.id,
            ),
        ]
        for budget in budgets:
            db_session.add(budget)
        await db_session.commit()

        response = await async_client.get("/budgets", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2


@pytest.mark.asyncio
class TestGetBudget:
    """Test getting single budget."""

    async def test_get_budget_success(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test getting budget by ID."""
        budget = Budget(
            name="Test Budget",
            amount=Decimal("1000"),
            currency="USD",
            period="monthly",
            start_date=date(2026, 2, 1),
            user_id=test_user.id,
        )
        db_session.add(budget)
        await db_session.commit()
        await db_session.refresh(budget)

        response = await async_client.get(f"/budgets/{budget.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == budget.id
        assert data["name"] == "Test Budget"


@pytest.mark.asyncio
class TestGetBudgetStatus:
    """Test getting budget status with spending."""

    async def test_get_budget_status(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test getting budget status."""
        budget = Budget(
            name="Food Budget",
            amount=Decimal("500"),
            currency="USD",
            period="monthly",
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 28),
            user_id=test_user.id,
        )
        db_session.add(budget)
        await db_session.commit()
        await db_session.refresh(budget)

        response = await async_client.get(f"/budgets/{budget.id}/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "spent" in data
        assert "remaining" in data
        assert "percentage" in data


@pytest.mark.asyncio
class TestUpdateBudget:
    """Test updating budget."""

    async def test_update_budget_success(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test updating budget."""
        budget = Budget(
            name="Old Budget",
            amount=Decimal("1000"),
            currency="USD",
            period="monthly",
            start_date=date(2026, 2, 1),
            user_id=test_user.id,
        )
        db_session.add(budget)
        await db_session.commit()
        await db_session.refresh(budget)

        response = await async_client.put(
            f"/budgets/{budget.id}",
            json={
                "name": "Updated Budget",
                "amount": 1500.00,
                "currency": "USD",
                "period": "monthly",
                "start_date": "2026-02-01",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Budget"
        assert float(data["amount"]) == 1500.00


@pytest.mark.asyncio
class TestDeleteBudget:
    """Test deleting budget."""

    async def test_delete_budget_success(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test deleting budget."""
        budget = Budget(
            name="To Delete",
            amount=Decimal("100"),
            currency="USD",
            period="monthly",
            start_date=date(2026, 2, 1),
            user_id=test_user.id,
        )
        db_session.add(budget)
        await db_session.commit()
        await db_session.refresh(budget)

        response = await async_client.delete(f"/budgets/{budget.id}", headers=auth_headers)
        assert response.status_code == 204
