"""Auto-categorization logic for transactions."""

import logging
import re
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, Rule, Transaction

logger = logging.getLogger(__name__)


async def categorize_transaction(
    transaction: Transaction, db: AsyncSession, user_id: int
) -> Optional[int]:
    """
    Auto-categorize a transaction based on rules and patterns.

    Args:
        transaction: Transaction to categorize
        db: Database session
        user_id: User ID for user-specific rules

    Returns:
        Category ID or None
    """
    # Get active rules for user, ordered by priority
    result = await db.execute(
        select(Rule)
        .where(Rule.user_id == user_id, Rule.is_active is True)
        .order_by(Rule.priority.desc(), Rule.id)
    )
    rules = result.scalars().all()

    # Try to match rules
    for rule in rules:
        if match_rule(transaction, rule):
            logger.info(
                f"Transaction {transaction.id} matched rule '{rule.name}' -> category {rule.category_id}"
            )
            return rule.category_id

    # Fallback: keyword-based categorization
    category_id = await keyword_based_categorization(transaction, db)
    if category_id:
        logger.info(
            f"Transaction {transaction.id} categorized by keywords -> category {category_id}"
        )
        return category_id

    logger.info(f"Transaction {transaction.id} could not be auto-categorized")
    return None


def match_rule(transaction: Transaction, rule: Rule) -> bool:
    """
    Check if a transaction matches a rule.

    Args:
        transaction: Transaction to check
        rule: Rule to match against

    Returns:
        True if matches, False otherwise
    """
    # Get the field value to check
    field_value = ""
    if rule.field == "merchant":
        field_value = transaction.merchant or ""
    elif rule.field == "description":
        field_value = transaction.description or ""
    else:
        return False

    # Match pattern (case-insensitive)
    pattern = rule.pattern.lower()
    field_value = field_value.lower()

    # Try regex match first
    try:
        if re.search(pattern, field_value):
            return True
    except re.error:
        # If regex fails, fall back to simple substring match
        if pattern in field_value:
            return True

    return False


async def keyword_based_categorization(transaction: Transaction, db: AsyncSession) -> Optional[int]:
    """
    Categorize based on common keywords.

    Args:
        transaction: Transaction to categorize
        db: Database session

    Returns:
        Category ID or None
    """
    # Common keyword mappings (lowercase)
    keyword_mappings = {
        "food": [
            "restaurant",
            "cafe",
            "coffee",
            "pizza",
            "burger",
            "food",
            "grocery",
            "supermarket",
            "market",
        ],
        "transport": ["uber", "lyft", "taxi", "gas", "fuel", "parking", "transit", "metro", "bus"],
        "shopping": ["amazon", "ebay", "store", "shop", "mall", "outlet"],
        "entertainment": ["netflix", "spotify", "cinema", "movie", "theater", "game", "steam"],
        "utilities": ["electric", "water", "gas", "internet", "phone", "mobile"],
        "health": ["pharmacy", "doctor", "hospital", "clinic", "medical", "dentist"],
        "rent": ["rent", "landlord", "lease"],
        "insurance": ["insurance", "premium"],
    }

    # Get merchant and description
    text = f"{transaction.merchant or ''} {transaction.description or ''}".lower()

    # Try to match keywords
    for category_name, keywords in keyword_mappings.items():
        for keyword in keywords:
            if keyword in text:
                # Find category by name
                result = await db.execute(
                    select(Category).where(Category.name.ilike(f"%{category_name}%"))
                )
                category = result.scalars().first()
                if category:
                    return category.id

    return None


async def bulk_categorize_transactions(db: AsyncSession, user_id: int, force: bool = False):
    """
    Categorize all uncategorized transactions for a user.

    Args:
        db: Database session
        user_id: User ID
        force: If True, recategorize all transactions (not just uncategorized)
    """
    # Get transactions to categorize
    query = select(Transaction).where(Transaction.user_id == user_id)

    if not force:
        query = query.where(Transaction.category_id.is_(None))

    result = await db.execute(query)
    transactions = result.scalars().all()

    categorized_count = 0
    for transaction in transactions:
        category_id = await categorize_transaction(transaction, db, user_id)
        if category_id:
            transaction.category_id = category_id
            categorized_count += 1

    await db.commit()
    logger.info(
        f"Categorized {categorized_count} out of {len(transactions)} transactions for user {user_id}"
    )

    return categorized_count
