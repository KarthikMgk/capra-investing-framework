"""update screener and rbi schema for story 2.1

Revision ID: c4d5e6f7a8b9
Revises: a1b2c3d4e5f6
Create Date: 2026-04-26 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'c4d5e6f7a8b9'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── screener_data ──────────────────────────────────────────────────────
    # Drop old columns from Story 1.2 template schema
    op.drop_column('screener_data', 'stock_symbol')
    op.drop_column('screener_data', 'pe_ratio')
    op.drop_column('screener_data', 'pb_ratio')
    op.drop_column('screener_data', 'roce')
    op.drop_column('screener_data', 'current_ratio')
    op.drop_column('screener_data', 'sales_growth')
    op.drop_column('screener_data', 'profit_growth')
    op.drop_column('screener_data', 'dividend_yield')

    # Add new columns matching Screener.in CSV schema
    op.add_column('screener_data', sa.Column('symbol', sa.String(length=20), nullable=False, server_default=''))
    op.add_column('screener_data', sa.Column('name', sa.Text(), nullable=True))
    op.add_column('screener_data', sa.Column('pe', sa.Float(), nullable=True))
    op.add_column('screener_data', sa.Column('pb', sa.Float(), nullable=True))
    op.add_column('screener_data', sa.Column('revenue_growth', sa.Float(), nullable=True))
    op.add_column('screener_data', sa.Column('promoter_holding', sa.Float(), nullable=True))

    # Remove the server default now that existing rows have been handled
    op.alter_column('screener_data', 'symbol', server_default=None)

    # Add index on upload_batch_id
    op.create_index('ix_screener_data_upload_batch_id', 'screener_data', ['upload_batch_id'])

    # ── rbi_macro_data ─────────────────────────────────────────────────────
    op.add_column('rbi_macro_data', sa.Column('date', sa.Date(), nullable=True))
    op.create_index('ix_rbi_macro_data_upload_batch_id', 'rbi_macro_data', ['upload_batch_id'])


def downgrade() -> None:
    op.drop_index('ix_rbi_macro_data_upload_batch_id', table_name='rbi_macro_data')
    op.drop_column('rbi_macro_data', 'date')

    op.drop_index('ix_screener_data_upload_batch_id', table_name='screener_data')
    op.drop_column('screener_data', 'promoter_holding')
    op.drop_column('screener_data', 'revenue_growth')
    op.drop_column('screener_data', 'pb')
    op.drop_column('screener_data', 'pe')
    op.drop_column('screener_data', 'name')
    op.drop_column('screener_data', 'symbol')

    op.add_column('screener_data', sa.Column('dividend_yield', sa.Float(), nullable=True))
    op.add_column('screener_data', sa.Column('profit_growth', sa.Float(), nullable=True))
    op.add_column('screener_data', sa.Column('sales_growth', sa.Float(), nullable=True))
    op.add_column('screener_data', sa.Column('current_ratio', sa.Float(), nullable=True))
    op.add_column('screener_data', sa.Column('roce', sa.Float(), nullable=True))
    op.add_column('screener_data', sa.Column('pb_ratio', sa.Float(), nullable=True))
    op.add_column('screener_data', sa.Column('pe_ratio', sa.Float(), nullable=True))
    op.add_column('screener_data', sa.Column('stock_symbol', sa.String(length=20), nullable=False, server_default=''))
    op.alter_column('screener_data', 'stock_symbol', server_default=None)
