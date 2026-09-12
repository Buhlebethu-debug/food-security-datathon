import os
import sys
from datetime import datetime
from airflow.decorators import dag, task

# Ensure src directory is available on path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)


@dag(
    dag_id="integrated_eat_trade_pipeline",
    schedule_interval="@monthly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["women_in_data", "eat_track", "trade_track"],
)
def food_security_pipeline():

  @task
  def extract_task():
    from extract import create_raw_datasets

    create_raw_datasets()

  @task
  def transform_and_load_task():
    from load import load_to_postgres

    load_to_postgres()

  extract_task() >> transform_and_load_task()


pipeline = food_security_pipeline()