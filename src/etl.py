"""
etl.py
------
Full ETL function, matching the course pattern: extract both source
tables, clean/transform them into analysis-ready tables, and load the
result into Postgres. This is the single function the Airflow DAG calls.
"""

from extract import extract_dbm_data, extract_sa_province_data
from transform import build_analysis_table
from load import load_all


def etl():
    print("Starting ETL run...")

    # Extract
    dbm_raw = extract_dbm_data()
    sa_raw = extract_sa_province_data()
    print(f"Extracted {len(dbm_raw)} DBM country rows, {len(sa_raw)} SA province rows")

    # Transform
    tables = build_analysis_table(dbm_raw, sa_raw)
    for name, df in tables.items():
        print(f"Transformed '{name}': {len(df)} rows")

    # Load
    load_all(tables)

    print("ETL run complete.")


if __name__ == "__main__":
    etl()
