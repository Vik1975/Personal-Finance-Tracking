"""Budget API endpoints."""

from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import BudgetCreate, BudgetResponse
from app.core.security import get_current_active_user
from app.db.base import get_db
from app.db.models import Budget, Category, Transaction, User

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=List[BudgetResponse])
async def list_budgets(
    current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
):
    """Get list of user's budgets."""
    result = await db.execute(
        select(Budget).where(Budget.user_id == current_user.id).order_by(Budget.start_date.desc())
    )
    budgets = result.scalars().all()

    return budgets


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new budget."""
    # Validate category if specified
    if budget_data.category_id:
        result = await db.execute(select(Category).where(Category.id == budget_data.category_id))
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    budget = Budget(user_id=current_user.id, **budget_data.model_dump())
    db.add(budget)
    await db.commit()
    await db.refresh(budget)

    return budget


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get budget by ID."""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    return budget


@router.get("/{budget_id}/status")
async def get_budget_status(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get budget status with spent amount and remaining."""
    # Get budget
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    # Calculate spent amount
    query = select(func.sum(Transaction.amount)).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.is_expense == True,
            Transaction.date >= budget.start_date,
        )
    )

    if budget.end_date:
        query = query.where(Transaction.date <= budget.end_date)

    if budget.category_id:
        query = query.where(Transaction.category_id == budget.category_id)

    result = await db.execute(query)
    spent = result.scalar() or Decimal("0")

    remaining = budget.amount - spent
    percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0

    return {
        "budget_id": budget.id,
        "budget_name": budget.name,
        "amount": float(budget.amount),
        "spent": float(spent),
        "remaining": float(remaining),
        "percentage": float(percentage),
        "period": budget.period,
        "start_date": budget.start_date,
        "end_date": budget.end_date,
        "is_exceeded": spent > budget.amount,
    }


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a budget."""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    # Validate category if changed
    if budget_data.category_id and budget_data.category_id != budget.category_id:
        result = await db.execute(select(Category).where(Category.id == budget_data.category_id))
        category = result.scalar_one_or_none()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Update fields
    for field, value in budget_data.model_dump().items():
        setattr(budget, field, value)

    await db.commit()
    await db.refresh(budget)

    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a budget."""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    await db.delete(budget)
    await db.commit()

    return None
