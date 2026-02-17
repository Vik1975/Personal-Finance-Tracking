"""Tests for categories API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Category


@pytest.mark.asyncio
class TestCreateCategory:
    """Test category creation."""

    async def test_create_category_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test successful category creation."""
        response = await async_client.post(
            "/categories",
            json={"name": "Groceries", "icon": "🛒", "color": "#FF5733"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Groceries"
        assert data["icon"] == "🛒"

    async def test_create_subcategory(
        self, async_client: AsyncClient, auth_headers: dict, test_categories: list
    ):
        """Test creating a subcategory."""
        parent = test_categories[0]
        response = await async_client.post(
            "/categories",
            json={"name": "Fresh Produce", "parent_id": parent.id, "icon": "🥕"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["parent_id"] == parent.id

    async def test_create_duplicate_category(
        self, async_client: AsyncClient, auth_headers: dict, test_categories: list
    ):
        """Test creating category with duplicate name."""
        response = await async_client.post(
            "/categories",
            json={"name": test_categories[0].name},
            headers=auth_headers,
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestListCategories:
    """Test listing categories."""

    async def test_list_all_categories(
        self, async_client: AsyncClient, auth_headers: dict, test_categories: list
    ):
        """Test listing all categories."""
        response = await async_client.get("/categories/all", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    async def test_list_top_level_categories(
        self, async_client: AsyncClient, auth_headers: dict, test_categories: list
    ):
        """Test listing top-level categories only."""
        response = await async_client.get("/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
class TestGetCategory:
    """Test getting single category."""

    async def test_get_category_success(
        self, async_client: AsyncClient, auth_headers: dict, test_categories: list
    ):
        """Test getting category by ID."""
        category = test_categories[0]
        response = await async_client.get(f"/categories/{category.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == category.id
        assert data["name"] == category.name

    async def test_get_nonexistent_category(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting non-existent category."""
        response = await async_client.get("/categories/99999", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateCategory:
    """Test updating category."""

    async def test_update_category_success(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        """Test updating category."""
        category = Category(name="Old Name", icon="📌")
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        response = await async_client.put(
            f"/categories/{category.id}",
            json={"name": "New Name", "icon": "✨"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["icon"] == "✨"

    async def test_update_category_prevent_circular_reference(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        """Test preventing category from being its own parent."""
        category = Category(name="Test Category")
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        response = await async_client.put(
            f"/categories/{category.id}",
            json={"name": "Test Category", "parent_id": category.id},
            headers=auth_headers,
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestDeleteCategory:
    """Test deleting category."""

    async def test_delete_category_success(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        """Test deleting category without children."""
        category = Category(name="To Delete")
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)

        response = await async_client.delete(f"/categories/{category.id}", headers=auth_headers)
        assert response.status_code == 204

    async def test_delete_category_with_children(
        self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession
    ):
        """Test deleting category with subcategories fails."""
        parent = Category(name="Parent")
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)

        child = Category(name="Child", parent_id=parent.id)
        db_session.add(child)
        await db_session.commit()

        response = await async_client.delete(f"/categories/{parent.id}", headers=auth_headers)
        assert response.status_code == 400
