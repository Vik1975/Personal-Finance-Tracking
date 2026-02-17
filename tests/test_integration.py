"""Integration tests covering full user workflows."""

import pytest
from decimal import Decimal
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


@pytest.mark.asyncio
class TestCompleteUserWorkflow:
    """Test complete user workflow from signup to analytics."""

    async def test_full_user_journey(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test complete user journey through the application."""
        # Step 1: Sign up
        signup_response = await async_client.post(
            "/auth/signup",
            json={
                "email": "journey@test.com",
                "full_name": "Journey Test",
                "password": "securepass123",
            },
        )
        assert signup_response.status_code == 201

        # Step 2: Login
        login_response = await async_client.post(
            "/auth/login",
            data={"username": "journey@test.com", "password": "securepass123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 3: Get user profile
        profile_response = await async_client.get("/auth/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == "journey@test.com"

        # Step 4: Create an account
        account_response = await async_client.post(
            "/accounts",
            json={"name": "Main Account", "account_type": "checking", "currency": "USD", "balance": 1000.00},
            headers=headers,
        )
        assert account_response.status_code == 201
        account_id = account_response.json()["id"]

        # Step 5: Create categories
        category_response = await async_client.post(
            "/categories",
            json={"name": "Food & Dining", "icon": "🍕", "color": "#FF5733"},
            headers=headers,
        )
        assert category_response.status_code == 201
        category_id = category_response.json()["id"]

        # Step 6: Create transactions
        transactions_data = [
            {"date": "2026-02-10", "amount": 50.00, "merchant": "Grocery Store", "account_id": account_id, "category_id": category_id},
            {"date": "2026-02-12", "amount": 30.00, "merchant": "Restaurant", "account_id": account_id, "category_id": category_id},
            {"date": "2026-02-15", "amount": 20.00, "merchant": "Coffee Shop", "account_id": account_id, "category_id": category_id},
        ]

        for txn_data in transactions_data:
            txn_response = await async_client.post(
                "/transactions",
                json={**txn_data, "currency": "USD", "is_expense": True},
                headers=headers,
            )
            assert txn_response.status_code == 201

        # Step 7: List transactions
        list_response = await async_client.get("/transactions", headers=headers)
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 3

        # Step 8: Get analytics summary
        analytics_response = await async_client.get(
            "/analytics/summary",
            params={"date_from": "2026-02-01", "date_to": "2026-02-28"},
            headers=headers,
        )
        assert analytics_response.status_code == 200
        summary = analytics_response.json()
        assert float(summary["total_expenses"]) >= 100.00

        # Step 9: Get category breakdown
        category_response = await async_client.get(
            "/analytics/categories",
            params={"date_from": "2026-02-01", "date_to": "2026-02-28", "is_expense": True},
            headers=headers,
        )
        assert category_response.status_code == 200

        # Step 10: Create a budget
        budget_response = await async_client.post(
            "/budgets",
            json={
                "name": "Monthly Food Budget",
                "amount": 500.00,
                "currency": "USD",
                "period": "monthly",
                "start_date": "2026-02-01",
                "end_date": "2026-02-28",
                "category_id": category_id,
            },
            headers=headers,
        )
        assert budget_response.status_code == 201
        budget_id = budget_response.json()["id"]

        # Step 11: Check budget status
        budget_status = await async_client.get(f"/budgets/{budget_id}/status", headers=headers)
        assert budget_status.status_code == 200
        status_data = budget_status.json()
        assert "spent" in status_data
        assert "remaining" in status_data


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling across endpoints."""

    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test that protected endpoints require authentication."""
        endpoints = [
            ("/transactions", "get"),
            ("/accounts", "get"),
            ("/budgets", "get"),
            ("/categories/all", "get"),
            ("/analytics/summary", "get"),
        ]

        for endpoint, method in endpoints:
            if method == "get":
                response = await async_client.get(endpoint)
            else:
                response = await async_client.post(endpoint, json={})
            assert response.status_code == 401

    async def test_invalid_resource_ids(self, async_client: AsyncClient, auth_headers: dict):
        """Test accessing non-existent resources."""
        invalid_id = 99999

        endpoints = [
            f"/transactions/{invalid_id}",
            f"/accounts/{invalid_id}",
            f"/budgets/{invalid_id}",
            f"/categories/{invalid_id}",
            f"/uploads/{invalid_id}",
        ]

        for endpoint in endpoints:
            response = await async_client.get(endpoint, headers=auth_headers)
            assert response.status_code == 404

    async def test_validation_errors(self, async_client: AsyncClient, auth_headers: dict):
        """Test validation errors."""
        # Invalid transaction (negative amount)
        response = await async_client.post(
            "/transactions",
            json={"date": "2026-02-17", "amount": -10.00, "currency": "USD", "is_expense": True},
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Invalid email format
        response = await async_client.post(
            "/auth/signup",
            json={"email": "invalid-email", "full_name": "Test", "password": "test123"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestDataIsolation:
    """Test that users can only access their own data."""

    async def test_user_data_isolation(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that users cannot access each other's data."""
        import random
        import string
        # Generate unique emails to avoid conflicts with other tests
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email1 = f"user1_{suffix}@test.com"
        email2 = f"user2_{suffix}@test.com"

        # Create two users (password must be 8+ chars)
        user1_response = await async_client.post(
            "/auth/signup",
            json={"email": email1, "full_name": "User 1", "password": "password123"},
        )
        assert user1_response.status_code == 201

        user2_response = await async_client.post(
            "/auth/signup",
            json={"email": email2, "full_name": "User 2", "password": "password123"},
        )
        assert user2_response.status_code == 201

        # Login as user1
        login1 = await async_client.post(
            "/auth/login",
            data={"username": email1, "password": "password123"},
        )
        assert login1.status_code == 200
        login1_data = login1.json()
        assert "access_token" in login1_data
        headers1 = {"Authorization": f"Bearer {login1_data['access_token']}"}

        # Login as user2
        login2 = await async_client.post(
            "/auth/login",
            data={"username": email2, "password": "password123"},
        )
        assert login2.status_code == 200
        login2_data = login2.json()
        assert "access_token" in login2_data
        headers2 = {"Authorization": f"Bearer {login2_data['access_token']}"}

        # User1 creates a transaction
        txn1 = await async_client.post(
            "/transactions",
            json={"date": "2026-02-17", "amount": 100.00, "currency": "USD", "is_expense": True},
            headers=headers1,
        )
        txn1_id = txn1.json()["id"]

        # User2 creates a transaction
        txn2 = await async_client.post(
            "/transactions",
            json={"date": "2026-02-17", "amount": 50.00, "currency": "USD", "is_expense": True},
            headers=headers2,
        )

        # User1 should only see their own transaction
        user1_txns = await async_client.get("/transactions", headers=headers1)
        assert len(user1_txns.json()) == 1

        # User2 cannot access User1's transaction
        user2_access = await async_client.get(f"/transactions/{txn1_id}", headers=headers2)
        assert user2_access.status_code == 404
