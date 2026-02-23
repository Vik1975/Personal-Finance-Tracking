"""Export functionality for transactions and analytics."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, date
from typing import Optional
import pandas as pd
import io

from app.db.base import get_db
from app.db.models import User, Transaction, Category
from app.core.security import get_current_active_user

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/transactions/csv")
async def export_transactions_csv(
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export transactions to CSV format.

    Filters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - category_id: Filter by category ID
    """
    # Build query
    query = select(Transaction).where(Transaction.user_id == current_user.id)

    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)
    if category_id:
        query = query.where(Transaction.category_id == category_id)

    query = query.order_by(Transaction.date.desc())

    # Execute query
    result = await db.execute(query)
    transactions = result.scalars().all()

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")

    # Convert to DataFrame
    data = []
    for txn in transactions:
        # Get category name
        if txn.category_id:
            cat_result = await db.execute(
                select(Category).where(Category.id == txn.category_id)
            )
            category = cat_result.scalar_one_or_none()
            category_name = category.name if category else "Uncategorized"
        else:
            category_name = "Uncategorized"

        data.append({
            "ID": txn.id,
            "Date": txn.date.strftime("%Y-%m-%d"),
            "Description": txn.description or "",
            "Amount": float(txn.amount),
            "Currency": txn.currency,
            "Type": txn.transaction_type,
            "Category": category_name,
            "Merchant": txn.merchant or "",
            "Notes": txn.notes or "",
            "Created At": txn.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(data)

    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    # Create response
    filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/transactions/excel")
async def export_transactions_excel(
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export transactions to Excel format with multiple sheets.

    Sheets:
    - Transactions: All transaction data
    - Summary: Summary statistics
    - By Category: Breakdown by category

    Filters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - category_id: Filter by category ID
    """
    # Build query
    query = select(Transaction).where(Transaction.user_id == current_user.id)

    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)
    if category_id:
        query = query.where(Transaction.category_id == category_id)

    query = query.order_by(Transaction.date.desc())

    # Execute query
    result = await db.execute(query)
    transactions = result.scalars().all()

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")

    # Prepare transactions data
    transactions_data = []
    for txn in transactions:
        # Get category name
        if txn.category_id:
            cat_result = await db.execute(
                select(Category).where(Category.id == txn.category_id)
            )
            category = cat_result.scalar_one_or_none()
            category_name = category.name if category else "Uncategorized"
        else:
            category_name = "Uncategorized"

        transactions_data.append({
            "ID": txn.id,
            "Date": txn.date.strftime("%Y-%m-%d"),
            "Description": txn.description or "",
            "Amount": float(txn.amount),
            "Currency": txn.currency,
            "Type": txn.transaction_type,
            "Category": category_name,
            "Merchant": txn.merchant or "",
            "Notes": txn.notes or "",
            "Created At": txn.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    df_transactions = pd.DataFrame(transactions_data)

    # Create summary data
    total_income = df_transactions[df_transactions["Type"] == "income"]["Amount"].sum()
    total_expense = df_transactions[df_transactions["Type"] == "expense"]["Amount"].sum()
    net_amount = total_income - total_expense

    summary_data = [
        {"Metric": "Total Income", "Amount": total_income},
        {"Metric": "Total Expenses", "Amount": total_expense},
        {"Metric": "Net Amount", "Amount": net_amount},
        {"Metric": "Transaction Count", "Amount": len(transactions)},
        {"Metric": "Average Transaction", "Amount": df_transactions["Amount"].mean()},
    ]
    df_summary = pd.DataFrame(summary_data)

    # Create category breakdown
    category_breakdown = df_transactions.groupby(["Category", "Type"])["Amount"].sum().reset_index()
    category_breakdown.columns = ["Category", "Type", "Total Amount"]
    category_breakdown = category_breakdown.sort_values("Total Amount", ascending=False)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Write each sheet
        df_transactions.to_excel(writer, sheet_name="Transactions", index=False)
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
        category_breakdown.to_excel(writer, sheet_name="By Category", index=False)

        # Get workbook and format
        workbook = writer.book

        # Format for currency
        currency_format = workbook.add_format({"num_format": "$#,##0.00"})

        # Auto-adjust column widths
        for sheet_name in ["Transactions", "Summary", "By Category"]:
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df_transactions.columns if sheet_name == "Transactions" else
                                      (df_summary.columns if sheet_name == "Summary" else category_breakdown.columns)):
                max_len = max(
                    df_transactions[col].astype(str).str.len().max() if sheet_name == "Transactions" else
                    (df_summary[col].astype(str).str.len().max() if sheet_name == "Summary" else
                     category_breakdown[col].astype(str).str.len().max()),
                    len(col)
                ) + 2
                worksheet.set_column(idx, idx, max_len)

    output.seek(0)

    # Create response
    filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/analytics/excel")
async def export_analytics_excel(
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export comprehensive analytics report to Excel.

    Includes:
    - Monthly trends
    - Category breakdown
    - Top merchants
    - Income vs Expenses comparison
    """
    # Build query
    query = select(Transaction).where(Transaction.user_id == current_user.id)

    if start_date:
        query = query.where(Transaction.date >= start_date)
    if end_date:
        query = query.where(Transaction.date <= end_date)

    query = query.order_by(Transaction.date.desc())

    # Execute query
    result = await db.execute(query)
    transactions = result.scalars().all()

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")

    # Prepare data
    data = []
    for txn in transactions:
        if txn.category_id:
            cat_result = await db.execute(
                select(Category).where(Category.id == txn.category_id)
            )
            category = cat_result.scalar_one_or_none()
            category_name = category.name if category else "Uncategorized"
        else:
            category_name = "Uncategorized"

        data.append({
            "Date": txn.date,
            "Amount": float(txn.amount),
            "Type": txn.transaction_type,
            "Category": category_name,
            "Merchant": txn.merchant or "Unknown",
            "Month": txn.date.strftime("%Y-%m"),
        })

    df = pd.DataFrame(data)

    # Monthly trends
    monthly_trends = df.groupby(["Month", "Type"])["Amount"].sum().reset_index()
    monthly_pivot = monthly_trends.pivot(index="Month", columns="Type", values="Amount").fillna(0)
    monthly_pivot["Net"] = monthly_pivot.get("income", 0) - monthly_pivot.get("expense", 0)

    # Category breakdown
    category_breakdown = df.groupby(["Category", "Type"])["Amount"].sum().reset_index()
    category_breakdown = category_breakdown.sort_values("Amount", ascending=False)

    # Top merchants (expenses only)
    merchant_breakdown = df[df["Type"] == "expense"].groupby("Merchant")["Amount"].sum().reset_index()
    merchant_breakdown = merchant_breakdown.sort_values("Amount", ascending=False).head(10)

    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        monthly_pivot.to_excel(writer, sheet_name="Monthly Trends")
        category_breakdown.to_excel(writer, sheet_name="Category Breakdown", index=False)
        merchant_breakdown.to_excel(writer, sheet_name="Top Merchants", index=False)

    output.seek(0)

    filename = f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
