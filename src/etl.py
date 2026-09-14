"""
Full ETL pipeline.

Extracts all source datasets, transforms them into analysis-ready tables,
and loads the results into PostgreSQL.

This is the single function called by the Airflow DAG.
"""

from extract import (
    extract_dbm_data,
    extract_sa_province_data,
    extract_empowerment_data,
    extract_trade_data
)

from transform import build_analysis_tables

from load import load_all


def etl():
    """
    Run the complete Extract -> Transform -> Load pipeline.
    """

    print("Starting ETL run...")

    # -----------------------------------------------------------------------
    # Extract
    # -----------------------------------------------------------------------

    dbm_raw = extract_dbm_data()
    sa_raw = extract_sa_province_data()
    empowerment_raw = extract_empowerment_data()
    trade_raw = extract_trade_data()

    print(
        f"Extracted {len(dbm_raw)} DBM country rows, "
        f"{len(sa_raw)} SA province rows, "
        f"{len(empowerment_raw)} empowerment rows, "
        f"{len(trade_raw)} trade rows"
    )

    # -----------------------------------------------------------------------
    # Transform
    # -----------------------------------------------------------------------

    tables = build_analysis_tables(
        dbm_raw,
        sa_raw,
        empowerment_raw,
        trade_raw
    )

    for name, df in tables.items():
        print(
            f"Transformed '{name}': "
            f"{len(df)} rows"
        )

    # -----------------------------------------------------------------------
    # Load
    # -----------------------------------------------------------------------

    load_all(tables)

    print("ETL run complete.")


if __name__ == "__main__":
    etl()