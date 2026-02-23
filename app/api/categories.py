"""Category API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import CategoryCreate, CategoryResponse
from app.core.security import get_current_active_user
from app.db.base import get_db
from app.db.models import Category, User

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    parent_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get list of categories (optionally filtered by parent)."""
    query = select(Category)

    if parent_id is not None:
        query = query.where(Category.parent_id == parent_id)
    else:
        # By default, return top-level categories (no parent)
        query = query.where(Category.parent_id.is_(None))

    query = query.order_by(Category.name)

    result = await db.execute(query)
    categories = result.scalars().all()

    return categories


@router.get("/all", response_model=List[CategoryResponse])
async def list_all_categories(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Get all categories (flat list)."""
    query = select(Category).order_by(Category.name)
    result = await db.execute(query)
    categories = result.scalars().all()

    return categories


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new category."""
    # Check if category with this name already exists
    result = await db.execute(select(Category).where(Category.name == category_data.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Category with this name already exists"
        )

    # Validate parent category exists if specified
    if category_data.parent_id:
        result = await db.execute(select(Category).where(Category.id == category_data.parent_id))
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent category not found"
            )

    category = Category(**category_data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return category


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get category by ID."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a category."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Check name uniqueness if changed
    if category_data.name != category.name:
        result = await db.execute(select(Category).where(Category.name == category_data.name))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists",
            )

    # Validate parent if changed
    if category_data.parent_id and category_data.parent_id != category.parent_id:
        # Prevent circular reference (category can't be its own parent)
        if category_data.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Category cannot be its own parent"
            )

        result = await db.execute(select(Category).where(Category.id == category_data.parent_id))
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent category not found"
            )

    # Update fields
    for field, value in category_data.model_dump().items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a category."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Check if category has children
    result = await db.execute(select(Category).where(Category.parent_id == category_id))
    children = result.scalars().first()
    if children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with subcategories",
        )

    await db.delete(category)
    await db.commit()

    return None
