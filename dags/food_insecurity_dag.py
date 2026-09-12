"""
food_insecurity_dag.py
-----------------------
Orchestrates the ETL pipeline (src/etl.py) using Airflow's TaskFlow API,
following the pattern from "Introduction to Data Engineering" (DataCamp):
  - @dag decorator with a start_date and a cron schedule
  - the ETL call wrapped in a @task
  - the dag() call at module level so Airflow's scheduler picks it up

Schedule choice: this pipeline's sources are published research snapshots
(a peer-reviewed paper's table, a Stats SA report), not live operational
data — there is nothing new to pull every midnight. A monthly schedule
("@monthly") is used instead of the course's daily example, matching how
often these upstream sources actually get revised. Swap the `schedule`
argument back to "0 0 * * *" if this pipeline is later pointed at a
live-updating source (e.g. a FAOSTAT API endpoint) instead of versioned
CSV snapshots.
"""

import sys
import os
from datetime import datetime

try:
    # Airflow 3.x preferred import path
    from airflow.sdk import dag, task
except ImportError:
    # Airflow 2.x fallback (the API taught in most current courses)
    from airflow.decorators import dag, task

# Make src/ importable from within the Airflow task
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))


@dag(
    dag_id="food_insecurity_etl",
    start_date=datetime(2026, 1, 1),
    schedule="@monthly",
    catchup=False,
    tags=["datathon", "food-insecurity", "double-burden"],
)
def food_insecurity_etl_dag():

    @task
    def run_etl():
        from etl import etl
        etl()

    run_etl()


food_insecurity_etl_dag()
