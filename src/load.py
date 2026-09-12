"""
load.py
-------
Loading layer of the ETL pipeline. Writes analysis-ready tables to
PostgreSQL using pandas' `.to_sql`, exactly as taught in the course
("Loading to Postgres" video): table name, engine, and an if_exists
strategy.

Connection settings are read from environment variables so credentials
are never hardcoded in source (see .env.example).
"""

import os
from sqlalchemy import create_engine
import pandas as pd


def get_engine():
    user = os.environ.get("PG_USER", "postgres")
    password = os.environ.get("PG_PASSWORD", "postgres")
    host = os.environ.get("PG_HOST", "localhost")
    port = os.environ.get("PG_PORT", "5432")
    db = os.environ.get("PG_DATABASE", "food_datathon")
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


def load_table(df: pd.DataFrame, table_name: str, engine=None, if_exists: str = "replace") -> None:
    """
    Load a single DataFrame into Postgres.

    if_exists="replace" is used here (rather than "append") because this
    pipeline's source data is a periodically-refreshed research snapshot,
    not an incrementing log — each run should represent the latest known
    state, not accumulate duplicate rows.
    """
    engine = engine or get_engine()
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    print(f"load_table: wrote {len(df)} rows to '{table_name}'")


def load_all(tables: dict, engine=None) -> None:
    engine = engine or get_engine()
    for name, df in tables.items():
        load_table(df, name, engine=engine)


if __name__ == "__main__":
    from extract import extract_dbm_data, extract_sa_province_data
    from transform import build_analysis_table

    tables = build_analysis_table(extract_dbm_data(), extract_sa_province_data())
    load_all(tables)
