"""added nullables in required mediciones_climaticas fields

Revision ID: cd90be82fe7a
Revises: de30876c8ac1
Create Date: 2026-05-25 14:38:56.648147

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'cd90be82fe7a'
down_revision = 'de30876c8ac1'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass