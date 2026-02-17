"""Tests for analytics API endpoints."""

import pytest
from datetime import date
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Transaction, Category


@pytest.mark.asyncio
class TestAnalyticsSummary:
    """Test analytics summary endpoint."""

    async def test_get_summary_with_transactions(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User, test_categories: list
    ):
        """Test getting analytics summary with transactions."""
        # Create test transactions
        transactions = [
            Transaction(
                user_id=test_user.id,
                date=date(2026, 2, 10),
                amount=Decimal("100"),
                currency="USD",
                merchant="Store A",
                is_expense=True,
            ),
            Transaction(
                user_id=test_user.id,
                date=date(2026, 2, 15),
                amount=Decimal("50"),
                currency="USD",
                merchant="Store B",
                is_expense=True,
            ),
            Transaction(
                user_id=test_user.id,
                date=date(2026, 2, 20),
                amount=Decimal("200"),
                currency="USD",
                merchant="Salary",
                is_expense=False,
            ),
        ]
        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        response = await async_client.get(
            "/analytics/summary",
            params={"date_from": "2026-02-01", "date_to": "2026-02-28"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "balance" in data
        assert "transactions_count" in data

    async def test_get_summary_without_auth(self, async_client: AsyncClient):
        """Test getting summary without authentication."""
        response = await async_client.get("/analytics/summary")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestCategoryBreakdown:
    """Test category breakdown endpoint."""

    async def test_get_category_breakdown(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User, test_categories: list
    ):
        """Test getting category breakdown."""
        # Create transactions with categories
        food_category = test_categories[0]
        transport_category = test_categories[1]

        transactions = [
            Transaction(
                user_id=test_user.id,
                category_id=food_category.id,
                date=date(2026, 2, 10),
                amount=Decimal("100"),
                currency="USD",
                is_expense=True,
            ),
            Transaction(
                user_id=test_user.id,
                category_id=transport_category.id,
                date=date(2026, 2, 15),
                amount=Decimal("50"),
                currency="USD",
                is_expense=True,
            ),
        ]
        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        response = await async_client.get(
            "/analytics/categories",
            params={"date_from": "2026-02-01", "date_to": "2026-02-28", "is_expense": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "category_name" in data[0]
            assert "total" in data[0]
            assert "percentage" in data[0]


@pytest.mark.asyncio
class TestTrends:
    """Test trends endpoint."""

    @pytest.mark.skip(reason="date_trunc not supported in SQLite, works in PostgreSQL")
    async def test_get_trends_monthly(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test getting monthly trends."""
        # Create transactions across multiple months
        transactions = [
            Transaction(
                user_id=test_user.id,
                date=date(2026, 1, 15),
                amount=Decimal("100"),
                currency="USD",
                is_expense=True,
            ),
            Transaction(
                user_id=test_user.id,
                date=date(2026, 2, 15),
                amount=Decimal("150"),
                currency="USD",
                is_expense=True,
            ),
        ]
        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        response = await async_client.get(
            "/analytics/trends",
            params={"period": "month", "count": 12},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "data" in data
        assert data["period"] == "month"


@pytest.mark.asyncio
class TestTopMerchants:
    """Test top merchants endpoint."""

    async def test_get_top_merchants(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test getting top merchants by spending."""
        # Create transactions with different merchants
        transactions = [
            Transaction(
                user_id=test_user.id,
                date=date(2026, 2, 10),
                amount=Decimal("100"),
                currency="USD",
                merchant="Walmart",
                is_expense=True,
            ),
            Transaction(
                user_id=test_user.id,
                date=date(2026, 2, 15),
                amount=Decimal("75"),
                currency="USD",
                merchant="Amazon",
                is_expense=True,
            ),
            Transaction(
                user_id=test_user.id,
                date=date(2026, 2, 20),
                amount=Decimal("50"),
                currency="USD",
                merchant="Walmart",
                is_expense=True,
            ),
        ]
        for txn in transactions:
            db_session.add(txn)
        await db_session.commit()

        response = await async_client.get(
            "/analytics/top-merchants",
            params={"limit": 10, "date_from": "2026-02-01", "date_to": "2026-02-28"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "merchants" in data
        merchants_list = data["merchants"]
        if len(merchants_list) > 0:
            assert "merchant" in merchants_list[0]
            assert "total" in merchants_list[0]
            assert "count" in merchants_list[0]
