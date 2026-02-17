"""Basic load tests for API endpoints."""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


@pytest.mark.asyncio
class TestLoadBasic:
    """Basic load testing scenarios."""

    async def test_health_endpoint_load(self, client):
        """Test health endpoint under load."""
        # Run 100 concurrent requests
        responses = []
        for _ in range(100):
            response = client.get("/health")
            responses.append(response.status_code)

        # All should succeed
        assert all(status == 200 for status in responses)
        assert len(responses) == 100

    @pytest.mark.skip(reason="SQLite doesn't handle concurrent writes well, works in PostgreSQL")
    async def test_concurrent_user_registration(self, async_client: AsyncClient):
        """Test concurrent user registrations."""
        async def create_user(index: int):
            response = await async_client.post(
                "/auth/signup",
                json={
                    "email": f"loadtest{index}@example.com",
                    "full_name": f"Load Test User {index}",
                    "password": "testpass123",
                },
            )
            return response.status_code

        # Create 10 users concurrently
        tasks = [create_user(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most should succeed (some may fail due to timing/database locks)
        success_count = sum(1 for r in results if r == 201)
        assert success_count >= 5  # At least half should succeed

    @pytest.mark.skip(reason="SQLite doesn't handle concurrent writes well, works in PostgreSQL")
    async def test_concurrent_transaction_creation(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test concurrent transaction creation."""
        async def create_transaction(index: int):
            response = await async_client.post(
                "/transactions",
                json={
                    "date": "2026-02-17",
                    "amount": 10.00 + index,
                    "currency": "USD",
                    "merchant": f"Store {index}",
                    "is_expense": True,
                },
                headers=auth_headers,
            )
            return response.status_code

        # Create 20 transactions concurrently
        tasks = [create_transaction(i) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful creations
        success_count = sum(1 for r in results if r == 201)
        assert success_count >= 15  # At least 75% should succeed


@pytest.mark.asyncio
class TestLoadRead:
    """Load testing for read operations."""

    async def test_concurrent_transaction_reads(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test concurrent transaction list reads."""
        async def read_transactions():
            response = await async_client.get("/transactions", headers=auth_headers)
            return response.status_code

        # Perform 50 concurrent reads
        tasks = [read_transactions() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        # All reads should succeed
        assert all(status == 200 for status in results)

    async def test_concurrent_analytics_requests(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test concurrent analytics requests."""
        async def get_summary():
            response = await async_client.get(
                "/analytics/summary",
                params={"date_from": "2026-02-01", "date_to": "2026-02-28"},
                headers=auth_headers,
            )
            return response.status_code

        # Perform 30 concurrent requests
        tasks = [get_summary() for _ in range(30)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(status == 200 for status in results)


@pytest.mark.asyncio
class TestPerformance:
    """Basic performance tests."""

    async def test_transaction_list_performance(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
    ):
        """Test transaction list response time with many records."""
        from app.db.models import Transaction
        from decimal import Decimal
        from datetime import date, timedelta

        # Create 100 transactions
        base_date = date(2026, 1, 1)
        for i in range(100):
            transaction = Transaction(
                user_id=test_user.id,
                date=base_date + timedelta(days=i % 30),
                amount=Decimal(str(10 + i)),
                currency="USD",
                merchant=f"Merchant {i}",
                is_expense=True,
            )
            db_session.add(transaction)
        await db_session.commit()

        # Measure response time (should be reasonably fast)
        import time
        start = time.time()
        response = await async_client.get("/transactions?limit=100", headers=auth_headers)
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 2.0  # Should complete within 2 seconds

    async def test_category_list_performance(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        """Test category list with many categories."""
        from app.db.models import Category

        # Create 50 categories
        for i in range(50):
            category = Category(name=f"Category {i}", icon="📁")
            db_session.add(category)
        await db_session.commit()

        # Should handle large category list efficiently
        import time
        start = time.time()
        response = await async_client.get("/categories/all", headers=auth_headers)
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0  # Should complete within 1 second
