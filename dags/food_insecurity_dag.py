import os
import sys
from datetime import datetime, timedelta
from airflow.sdk import dag, task

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

default_args = {"retries": 1, "retry_delay": timedelta(minutes=5)}


@dag(
    dag_id="integrated_eat_trade_pipeline",
    schedule="@monthly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["women_in_data", "eat_track", "trade_track"],
)
def food_security_pipeline():

    @task
    def extract_task():
        from extract import create_raw_datasets
        create_raw_datasets()

    @task
    def transform_task():
        from transform import save_transformed
        save_transformed()

    @task
    def load_task():
        from load import load_to_postgres
        load_to_postgres()

    extract_task() >> transform_task() >> load_task()


pipeline = food_security_pipeline()