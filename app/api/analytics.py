"""Analytics API endpoints."""

from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, extract

from app.core.security import get_current_active_user
from app.db.base import get_db
from app.db.models import User, Transaction, Category
from app.api.schemas import AnalyticsSummary, CategorySummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    account_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get financial summary for a period."""
    # Default to current month if no dates provided
    if not date_from:
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()

    # Base query
    base_query = select(Transaction).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.date >= date_from,
            Transaction.date <= date_to
        )
    )

    if account_id:
        base_query = base_query.where(Transaction.account_id == account_id)

    # Get total income
    income_query = select(func.sum(Transaction.amount)).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
            Transaction.is_expense == False
        )
    )
    if account_id:
        income_query = income_query.where(Transaction.account_id == account_id)

    result = await db.execute(income_query)
    total_income = result.scalar() or Decimal("0")

    # Get total expenses
    expense_query = select(func.sum(Transaction.amount)).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
            Transaction.is_expense == True
        )
    )
    if account_id:
        expense_query = expense_query.where(Transaction.account_id == account_id)

    result = await db.execute(expense_query)
    total_expenses = result.scalar() or Decimal("0")

    # Get transaction count
    count_query = select(func.count(Transaction.id)).where(
        and_(
            Transaction.user_id == current_user.id,
            Transaction.date >= date_from,
            Transaction.date <= date_to
        )
    )
    if account_id:
        count_query = count_query.where(Transaction.account_id == account_id)

    result = await db.execute(count_query)
    transactions_count = result.scalar() or 0

    balance = total_income - total_expenses

    return AnalyticsSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        transactions_count=transactions_count,
        period_start=date_from,
        period_end=date_to,
    )


@router.get("/categories", response_model=List[CategorySummary])
async def get_category_breakdown(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    is_expense: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get spending/income breakdown by category."""
    # Default to current month
    if not date_from:
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()

    # Query category totals
    query = (
        select(
            Transaction.category_id,
            Category.name,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
                Transaction.is_expense == is_expense
            )
        )
        .group_by(Transaction.category_id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    # Calculate total for percentages
    grand_total = sum(row.total for row in rows) or Decimal("0")

    # Build response
    summaries = []
    for row in rows:
        percentage = (row.total / grand_total * 100) if grand_total > 0 else 0
        summaries.append(
            CategorySummary(
                category_id=row.category_id,
                category_name=row.name or "Uncategorized",
                total=row.total,
                count=row.count,
                percentage=float(percentage),
            )
        )

    return summaries


@router.get("/trends")
async def get_trends(
    period: str = Query("month", pattern="^(day|week|month|year)$"),
    count: int = Query(12, ge=1, le=365),
    is_expense: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get spending/income trends over time."""
    # Determine grouping based on period
    if period == "year":
        group_func = extract("year", Transaction.date)
        label = "year"
    elif period == "month":
        group_func = func.date_trunc("month", Transaction.date)
        label = "month"
    elif period == "week":
        group_func = func.date_trunc("week", Transaction.date)
        label = "week"
    else:  # day
        group_func = Transaction.date
        label = "date"

    # Build query
    query = (
        select(
            group_func.label("period"),
            func.sum(Transaction.amount).label("total")
        )
        .where(Transaction.user_id == current_user.id)
    )

    if is_expense is not None:
        query = query.where(Transaction.is_expense == is_expense)

    query = (
        query.group_by("period")
        .order_by("period")
        .limit(count)
    )

    result = await db.execute(query)
    rows = result.all()

    # Format response
    trends = []
    for row in rows:
        period_value = row.period
        if isinstance(period_value, datetime):
            period_value = period_value.date().isoformat()
        elif isinstance(period_value, date):
            period_value = period_value.isoformat()

        trends.append({
            label: str(period_value),
            "total": float(row.total),
        })

    return {"period": period, "data": trends}


@router.get("/top-merchants")
async def get_top_merchants(
    limit: int = Query(10, ge=1, le=100),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get top merchants by spending."""
    # Default to current month
    if not date_from:
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()

    query = (
        select(
            Transaction.merchant,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        )
        .where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
                Transaction.is_expense == True,
                Transaction.merchant.isnot(None)
            )
        )
        .group_by(Transaction.merchant)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    merchants = []
    for row in rows:
        merchants.append({
            "merchant": row.merchant,
            "total": float(row.total),
            "count": row.count,
        })

    return {"merchants": merchants}
