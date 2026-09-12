import os
import pandas as pd
from sqlalchemy import create_engine
from transform import transform_all


def load_to_postgres():
  # Postgres.app automatically uses your macOS username and default port 5432
  db_user = os.getenv("USER", "postgres")
  db_pass = ""  # Postgres.app leaves local password empty by default
  db_host = "localhost"
  db_port = "5432"
  db_name = "food_datathon"

  db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
  engine = create_engine(db_url)

  # Fetch transformed analytical layer from Step 2
  integrated_df = transform_all()

  # Write table directly to PostgreSQL
  integrated_df.to_sql(
      "integrated_eat_trade_matrix", engine, if_exists="replace", index=False
  )
  print(
      "✓ Loaded table 'integrated_eat_trade_matrix' to PostgreSQL"
      " successfully!"
  )


if __name__ == "__main__":
  load_to_postgres()