import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from extract_household import (
    extract_dbm_data,
    extract_sa_province_data,
    extract_empowerment_data,
    extract_trade_data,
)
from transform_household import build_analysis_tables

load_dotenv()

VIEW_SQL = """
CREATE OR REPLACE VIEW view_household_dbm_analysis AS
SELECT
    country,
    country_code,
    dbm_pct,
    female_decision_score,
    crop_diversity_index,
    net_staple_import_dependency_pct,
    nutritional_resilience_index
FROM country_nutritional_resilience
"""


def get_engine():
    db_user = os.environ.get("PG_USER", os.getenv("USER", "postgres"))
    db_pass = os.environ.get("PG_PASSWORD", "")
    db_host = os.environ.get("PG_HOST", "localhost")
    db_port = os.environ.get("PG_PORT", "5432")
    db_name = os.environ.get("PG_DATABASE", "food_datathon")
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(db_url)


def load_all(tables: dict = None):
    """
    Loads the three household-analysis tables into Postgres:
      - country_nutritional_resilience  (real 4-country NRI vs. DBM test)
      - dbm_by_country_household         (22-country Bawuah et al. DBM table)
      - sa_food_insecurity_by_province   (Stats SA provincial food insecurity)

    Also rebuilds a summary view over country_nutritional_resilience.
    """
    if tables is None:
        dbm = extract_dbm_data()
        sa = extract_sa_province_data()
        empowerment = extract_empowerment_data()
        trade = extract_trade_data()
        tables = build_analysis_tables(dbm, sa, empowerment, trade)

    engine = get_engine()

    try:
        with engine.begin() as conn:
            conn.execute(text("DROP VIEW IF EXISTS view_household_dbm_analysis CASCADE"))

            tables["country_nutritional_resilience"].to_sql(
                "country_nutritional_resilience", conn, if_exists="replace", index=False
            )
            tables["dbm_by_country"].to_sql(
                "dbm_by_country_household", conn, if_exists="replace", index=False
            )
            tables["sa_food_insecurity_by_province"].to_sql(
                "sa_food_insecurity_by_province", conn, if_exists="replace", index=False
            )

            conn.execute(text(VIEW_SQL))

        print("\u2713 Loaded household-DBM tables and rebuilt view_household_dbm_analysis successfully")
    except Exception as e:
        print(f"\u2717 Household load failed: {e}")
        raise


if __name__ == "__main__":
    load_all()
