"""add kite_settings table

Revision ID: a1b2c3d4e5f6
Revises: c9005076345a
Create Date: 2026-04-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c9005076345a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('kite_settings',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('api_key_encrypted', sa.Text(), nullable=False),
    sa.Column('access_token_encrypted', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('kite_settings')
