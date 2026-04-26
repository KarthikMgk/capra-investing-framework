"""
Schema verification tests — assert every capra table, column, and index
exists after running alembic upgrade head.
"""
import pytest
from sqlalchemy import inspect, text
from sqlmodel import Session

from app.core.db import engine


@pytest.fixture(scope="module")
def inspector():
    return inspect(engine)


def test_all_five_tables_exist(inspector):
    tables = inspector.get_table_names()
    for table in ("users", "score_snapshots", "screener_data", "rbi_macro_data", "revoked_tokens"):
        assert table in tables, f"Table '{table}' is missing"


# ── users ──────────────────────────────────────────────────────────────────

def test_users_columns(inspector):
    cols = {c["name"] for c in inspector.get_columns("users")}
    required = {"id", "email", "hashed_password", "role", "is_active", "created_at", "updated_at"}
    assert required <= cols, f"Missing columns: {required - cols}"


def test_users_email_index(inspector):
    indexes = {idx["name"] for idx in inspector.get_indexes("users")}
    assert any("email" in name for name in indexes), "No index on users.email"


# ── score_snapshots ─────────────────────────────────────────────────────────

def test_score_snapshots_columns(inspector):
    cols = {c["name"] for c in inspector.get_columns("score_snapshots")}
    required = {
        "id", "stock_symbol", "composite_score", "signal", "position_size",
        "computation_timestamp", "kite_snapshot_ts", "screener_csv_ts", "rbi_csv_ts",
        "factor_breakdown",
    }
    assert required <= cols, f"Missing columns: {required - cols}"


def test_ix_score_snapshots_stock_symbol(inspector):
    indexes = {idx["name"] for idx in inspector.get_indexes("score_snapshots")}
    assert "ix_score_snapshots_stock_symbol" in indexes


# ── screener_data ────────────────────────────────────────────────────────────

def test_screener_data_columns(inspector):
    cols = {c["name"] for c in inspector.get_columns("screener_data")}
    required = {
        "id", "upload_batch_id", "uploaded_at",
        "symbol", "name", "pe", "pb", "eps", "roe",
        "debt_to_equity", "revenue_growth", "promoter_holding",
    }
    assert required <= cols, f"Missing columns: {required - cols}"


# ── rbi_macro_data ───────────────────────────────────────────────────────────

def test_rbi_macro_data_columns(inspector):
    cols = {c["name"] for c in inspector.get_columns("rbi_macro_data")}
    required = {"id", "upload_batch_id", "uploaded_at", "date", "repo_rate", "credit_growth", "liquidity_indicator"}
    assert required <= cols, f"Missing columns: {required - cols}"


# ── revoked_tokens ───────────────────────────────────────────────────────────

def test_revoked_tokens_columns(inspector):
    cols = {c["name"] for c in inspector.get_columns("revoked_tokens")}
    required = {"id", "jti", "expires_at"}
    assert required <= cols, f"Missing columns: {required - cols}"


def test_ix_revoked_tokens_jti(inspector):
    indexes = {idx["name"] for idx in inspector.get_indexes("revoked_tokens")}
    assert "ix_revoked_tokens_jti" in indexes


# ── get_session integration ──────────────────────────────────────────────────

def test_get_session_yields_valid_session():
    from app.database import get_session
    gen = get_session()
    session = next(gen)
    assert isinstance(session, Session)
    result = session.exec(text("SELECT 1")).scalar()
    assert result == 1
    try:
        next(gen)
    except StopIteration:
        pass
