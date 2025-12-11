"""Seed default categories

Revision ID: 002
Revises: 001
Create Date: 2025-01-01 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create categories table reference
    categories = sa.table('categories',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('parent_id', sa.Integer),
        sa.column('icon', sa.String),
        sa.column('color', sa.String),
        sa.column('created_at', sa.DateTime),
    )

    # Default categories with icons and colors
    now = datetime.utcnow()

    # Insert parent categories
    op.bulk_insert(categories, [
        {'id': 1, 'name': 'Food & Dining', 'parent_id': None, 'icon': '🍔', 'color': '#FF6B6B', 'created_at': now},
        {'id': 2, 'name': 'Transport', 'parent_id': None, 'icon': '🚗', 'color': '#4ECDC4', 'created_at': now},
        {'id': 3, 'name': 'Shopping', 'parent_id': None, 'icon': '🛍️', 'color': '#95E1D3', 'created_at': now},
        {'id': 4, 'name': 'Entertainment', 'parent_id': None, 'icon': '🎮', 'color': '#F38181', 'created_at': now},
        {'id': 5, 'name': 'Utilities', 'parent_id': None, 'icon': '💡', 'color': '#AA96DA', 'created_at': now},
        {'id': 6, 'name': 'Health', 'parent_id': None, 'icon': '🏥', 'color': '#FCBAD3', 'created_at': now},
        {'id': 7, 'name': 'Housing', 'parent_id': None, 'icon': '🏠', 'color': '#A8D8EA', 'created_at': now},
        {'id': 8, 'name': 'Income', 'parent_id': None, 'icon': '💰', 'color': '#77DD77', 'created_at': now},
        {'id': 9, 'name': 'Education', 'parent_id': None, 'icon': '📚', 'color': '#FFB347', 'created_at': now},
        {'id': 10, 'name': 'Personal', 'parent_id': None, 'icon': '👤', 'color': '#DDA0DD', 'created_at': now},
    ])

    # Insert subcategories
    op.bulk_insert(categories, [
        # Food & Dining (1)
        {'id': 11, 'name': 'Restaurants', 'parent_id': 1, 'icon': '🍽️', 'color': '#FF6B6B', 'created_at': now},
        {'id': 12, 'name': 'Groceries', 'parent_id': 1, 'icon': '🛒', 'color': '#FF6B6B', 'created_at': now},
        {'id': 13, 'name': 'Coffee Shops', 'parent_id': 1, 'icon': '☕', 'color': '#FF6B6B', 'created_at': now},
        {'id': 14, 'name': 'Fast Food', 'parent_id': 1, 'icon': '🍕', 'color': '#FF6B6B', 'created_at': now},

        # Transport (2)
        {'id': 21, 'name': 'Public Transit', 'parent_id': 2, 'icon': '🚇', 'color': '#4ECDC4', 'created_at': now},
        {'id': 22, 'name': 'Taxi/Ride Share', 'parent_id': 2, 'icon': '🚕', 'color': '#4ECDC4', 'created_at': now},
        {'id': 23, 'name': 'Gas/Fuel', 'parent_id': 2, 'icon': '⛽', 'color': '#4ECDC4', 'created_at': now},
        {'id': 24, 'name': 'Parking', 'parent_id': 2, 'icon': '🅿️', 'color': '#4ECDC4', 'created_at': now},

        # Shopping (3)
        {'id': 31, 'name': 'Clothing', 'parent_id': 3, 'icon': '👕', 'color': '#95E1D3', 'created_at': now},
        {'id': 32, 'name': 'Electronics', 'parent_id': 3, 'icon': '💻', 'color': '#95E1D3', 'created_at': now},
        {'id': 33, 'name': 'Online Shopping', 'parent_id': 3, 'icon': '📦', 'color': '#95E1D3', 'created_at': now},

        # Entertainment (4)
        {'id': 41, 'name': 'Streaming Services', 'parent_id': 4, 'icon': '📺', 'color': '#F38181', 'created_at': now},
        {'id': 42, 'name': 'Movies/Theater', 'parent_id': 4, 'icon': '🎬', 'color': '#F38181', 'created_at': now},
        {'id': 43, 'name': 'Games', 'parent_id': 4, 'icon': '🎯', 'color': '#F38181', 'created_at': now},

        # Utilities (5)
        {'id': 51, 'name': 'Electricity', 'parent_id': 5, 'icon': '⚡', 'color': '#AA96DA', 'created_at': now},
        {'id': 52, 'name': 'Water', 'parent_id': 5, 'icon': '💧', 'color': '#AA96DA', 'created_at': now},
        {'id': 53, 'name': 'Internet', 'parent_id': 5, 'icon': '🌐', 'color': '#AA96DA', 'created_at': now},
        {'id': 54, 'name': 'Phone', 'parent_id': 5, 'icon': '📱', 'color': '#AA96DA', 'created_at': now},

        # Health (6)
        {'id': 61, 'name': 'Doctor', 'parent_id': 6, 'icon': '👨‍⚕️', 'color': '#FCBAD3', 'created_at': now},
        {'id': 62, 'name': 'Pharmacy', 'parent_id': 6, 'icon': '💊', 'color': '#FCBAD3', 'created_at': now},
        {'id': 63, 'name': 'Gym/Fitness', 'parent_id': 6, 'icon': '💪', 'color': '#FCBAD3', 'created_at': now},

        # Housing (7)
        {'id': 71, 'name': 'Rent/Mortgage', 'parent_id': 7, 'icon': '🔑', 'color': '#A8D8EA', 'created_at': now},
        {'id': 72, 'name': 'Home Insurance', 'parent_id': 7, 'icon': '🛡️', 'color': '#A8D8EA', 'created_at': now},
        {'id': 73, 'name': 'Maintenance', 'parent_id': 7, 'icon': '🔧', 'color': '#A8D8EA', 'created_at': now},

        # Income (8)
        {'id': 81, 'name': 'Salary', 'parent_id': 8, 'icon': '💵', 'color': '#77DD77', 'created_at': now},
        {'id': 82, 'name': 'Freelance', 'parent_id': 8, 'icon': '💼', 'color': '#77DD77', 'created_at': now},
        {'id': 83, 'name': 'Investments', 'parent_id': 8, 'icon': '📈', 'color': '#77DD77', 'created_at': now},

        # Education (9)
        {'id': 91, 'name': 'Tuition', 'parent_id': 9, 'icon': '🎓', 'color': '#FFB347', 'created_at': now},
        {'id': 92, 'name': 'Books', 'parent_id': 9, 'icon': '📖', 'color': '#FFB347', 'created_at': now},
        {'id': 93, 'name': 'Courses', 'parent_id': 9, 'icon': '💡', 'color': '#FFB347', 'created_at': now},
    ])


def downgrade() -> None:
    # Delete all seeded categories
    op.execute("DELETE FROM categories WHERE id <= 100")
