"""Accès base de données PostgreSQL."""

from contextlib import contextmanager
from typing import Generator

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from p13.config import DATABASE_URL

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


@contextmanager
def get_connection() -> Generator:
    engine = get_engine()
    with engine.connect() as conn:
        yield conn


def read_sql(query: str, params: dict | None = None) -> pd.DataFrame:
    return pd.read_sql(text(query), get_engine(), params=params or {})


def execute_sql(query: str, params: dict | None = None) -> None:
    with get_connection() as conn:
        conn.execute(text(query), params or {})
        conn.commit()


def truncate_table(table: str) -> None:
    execute_sql(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")


def log_etl_run(table_name: str, rows: int, status: str, message: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            text(
                "INSERT INTO etl_runs (table_name, rows_loaded, status, message) "
                "VALUES (:table, :rows, :status, :msg)"
            ),
            {"table": table_name, "rows": rows, "status": status, "msg": message},
        )
        conn.commit()
