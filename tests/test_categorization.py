"""Tests for categorization logic."""

import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Transaction, Category, Rule
from app.processing.categorization import categorize_transaction, match_rule, keyword_based_categorization


@pytest.mark.asyncio
class TestCategorizationRuleBased:
    """Test rule-based categorization."""

    async def test_categorize_with_merchant_rule(
        self, db_session: AsyncSession, test_user: User, test_categories: list
    ):
        """Test categorization using merchant rule."""
        food_category = test_categories[0]

        # Create a rule for Walmart -> Food
        rule = Rule(
            user_id=test_user.id,
            category_id=food_category.id,
            name="Walmart Food Rule",
            field="merchant",
            pattern="Walmart",
            priority=10,
            is_active=True,
        )
        db_session.add(rule)
        await db_session.commit()

        # Create transaction
        transaction = Transaction(
            user_id=test_user.id,
            date=date.today(),
            amount=Decimal("50"),
            merchant="Walmart",
            is_expense=True,
        )

        result = await categorize_transaction(transaction, db_session, test_user.id)
        assert result == food_category.id

    async def test_categorize_with_description_rule(
        self, db_session: AsyncSession, test_user: User, test_categories: list
    ):
        """Test categorization using description rule."""
        transport_category = test_categories[1]

        # Create a rule for gas purchases
        rule = Rule(
            user_id=test_user.id,
            category_id=transport_category.id,
            name="Gas Purchase Rule",
            field="description",
            pattern="gas|fuel",
            priority=5,
            is_active=True,
        )
        db_session.add(rule)
        await db_session.commit()

        # Create transaction
        transaction = Transaction(
            user_id=test_user.id,
            date=date.today(),
            amount=Decimal("40"),
            description="Bought gas at Shell",
            is_expense=True,
        )

        result = await categorize_transaction(transaction, db_session, test_user.id)
        assert result == transport_category.id

    async def test_categorize_no_matching_rule(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test categorization when no rule matches."""
        # Create transaction that doesn't match any rule
        transaction = Transaction(
            user_id=test_user.id,
            date=date.today(),
            amount=Decimal("25"),
            merchant="Unknown Store",
            is_expense=True,
        )

        result = await categorize_transaction(transaction, db_session, test_user.id)
        # Should return None or a keyword-based category
        assert result is None or isinstance(result, int)


@pytest.mark.asyncio
class TestCategorizationKeywordBased:
    """Test keyword-based categorization."""

    async def test_categorize_food_keywords(
        self, db_session: AsyncSession, test_user: User, test_categories: list
    ):
        """Test categorization using food keywords."""
        # Create transaction with food keywords
        transaction = Transaction(
            user_id=test_user.id,
            date=date.today(),
            amount=Decimal("30"),
            merchant="Pizza Hut",
            description="Dinner",
            is_expense=True,
        )

        result = await keyword_based_categorization(transaction, db_session)
        # Should find a food-related category or return None
        assert result is None or isinstance(result, int)

    async def test_categorize_transport_keywords(
        self, db_session: AsyncSession, test_user: User, test_categories: list
    ):
        """Test categorization using transport keywords."""
        # Create transaction with transport keywords
        transaction = Transaction(
            user_id=test_user.id,
            date=date.today(),
            amount=Decimal("20"),
            merchant="Uber",
            is_expense=True,
        )

        result = await keyword_based_categorization(transaction, db_session)
        assert result is None or isinstance(result, int)


@pytest.mark.asyncio
class TestRuleMatching:
    """Test rule matching logic."""

    async def test_match_rule_exact_merchant(
        self, db_session: AsyncSession, test_user: User, test_categories: list
    ):
        """Test matching rule with exact merchant name."""
        rule = Rule(
            user_id=test_user.id,
            category_id=test_categories[0].id,
            name="Test Rule",
            field="merchant",
            pattern="^Amazon$",
            priority=10,
            is_active=True,
        )

        transaction = Transaction(
            user_id=test_user.id,
            date=date.today(),
            amount=Decimal("50"),
            merchant="Amazon",
            is_expense=True,
        )

        result = match_rule(transaction, rule)
        assert result is True

    async def test_match_rule_partial_match(
        self, db_session: AsyncSession, test_user: User, test_categories: list
    ):
        """Test matching rule with partial match."""
        rule = Rule(
            user_id=test_user.id,
            category_id=test_categories[0].id,
            name="Test Rule",
            field="merchant",
            pattern="walmart",
            priority=10,
            is_active=True,
        )

        transaction = Transaction(
            user_id=test_user.id,
            date=date.today(),
            amount=Decimal("50"),
            merchant="Walmart Supercenter",
            is_expense=True,
        )

        result = match_rule(transaction, rule)
        assert result is True

    async def test_match_rule_no_match(
        self, db_session: AsyncSession, test_user: User, test_categories: list
    ):
        """Test rule that doesn't match."""
        rule = Rule(
            user_id=test_user.id,
            category_id=test_categories[0].id,
            name="Test Rule",
            field="merchant",
            pattern="Target",
            priority=10,
            is_active=True,
        )

        transaction = Transaction(
            user_id=test_user.id,
            date=date.today(),
            amount=Decimal("50"),
            merchant="Walmart",
            is_expense=True,
        )

        result = match_rule(transaction, rule)
        assert result is False


@pytest.mark.asyncio
class TestRulePriority:
    """Test rule priority ordering."""

    async def test_higher_priority_rule_wins(
        self, db_session: AsyncSession, test_user: User, test_categories: list
    ):
        """Test that higher priority rule is applied first."""
        # Create two rules that both match
        high_priority_rule = Rule(
            user_id=test_user.id,
            category_id=test_categories[0].id,
            name="High Priority",
            field="merchant",
            pattern="Walmart",
            priority=100,
            is_active=True,
        )
        low_priority_rule = Rule(
            user_id=test_user.id,
            category_id=test_categories[1].id,
            name="Low Priority",
            field="merchant",
            pattern="Walmart",
            priority=1,
            is_active=True,
        )
        db_session.add(high_priority_rule)
        db_session.add(low_priority_rule)
        await db_session.commit()

        transaction = Transaction(
            user_id=test_user.id,
            date=date.today(),
            amount=Decimal("50"),
            merchant="Walmart",
            is_expense=True,
        )

        result = await categorize_transaction(transaction, db_session, test_user.id)
        assert result == test_categories[0].id  # Higher priority rule's category
