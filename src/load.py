import os
import pandas as pd
from sqlalchemy import create_engine
from transform import transform_all


def get_engine():
    user = os.environ.get("PG_USER", "postgres")
    password = os.environ.get("PG_PASSWORD", "postgres")
    host = os.environ.get("PG_HOST", "localhost")
    port = os.environ.get("PG_PORT", "5433")
    db = os.environ.get("PG_DATABASE", "food_datathon")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


def load_to_postgres():
    engine = get_engine()

    # Fetch transformed analytical layer from Step 2
    integrated_df = transform_all()

    # Write table directly to PostgreSQL
    integrated_df.to_sql(
        "integrated_eat_trade_matrix",
        engine,
        if_exists="replace",
        index=False
    )

    print(
        "✓ Loaded table 'integrated_eat_trade_matrix' to PostgreSQL"
        " successfully!"
    )


if __name__ == "__main__":
    load_to_postgres()