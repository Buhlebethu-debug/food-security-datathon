import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from transform import PROCESSED_PATH

load_dotenv()

VIEW_SQL = """
CREATE OR REPLACE VIEW view_eat_trade_empowerment_matrix AS
SELECT
    country,
    country_code,
    dbm_category,
    dbm_score,
    female_decision_score,
    crop_diversity_index,
    net_staple_import_dependency_pct,
    nutritional_resilience_index,
    source_years,
    data_years_mismatched
FROM integrated_eat_trade_matrix
"""


def get_engine():
    db_user = os.environ.get("PG_USER", os.getenv("USER", "postgres"))
    db_pass = os.environ.get("PG_PASSWORD", "")
    db_host = os.environ.get("PG_HOST", "localhost")
    db_port = os.environ.get("PG_PORT", "5432")
    db_name = os.environ.get("PG_DATABASE", "food_datathon")
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(db_url)


def load_to_postgres():
    if not os.path.exists(PROCESSED_PATH):
        raise FileNotFoundError(f"{PROCESSED_PATH} not found \u2014 run `python src/transform.py` first.")

    integrated_df = pd.read_csv(PROCESSED_PATH)
    engine = get_engine()

    try:
        with engine.begin() as conn:
            conn.execute(text("DROP VIEW IF EXISTS view_eat_trade_empowerment_matrix CASCADE"))
            integrated_df.to_sql("integrated_eat_trade_matrix", conn, if_exists="replace", index=False)
            conn.execute(text(VIEW_SQL))
        print("\u2713 Loaded 'integrated_eat_trade_matrix' and rebuilt the analytical view successfully")
    except Exception as e:
        print(f"\u2717 Load failed: {e}")
        raise


if __name__ == "__main__":
    load_to_postgres()