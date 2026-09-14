import os
from pathlib import Path

from sqlalchemy import create_engine, text


def get_engine():
    user = os.getenv("PG_USER", "postgres")
    password = os.getenv("PG_PASSWORD", "postgres")
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    database = os.getenv("PG_DATABASE", "food_datathon")

    database_url = (
        f"postgresql://{user}:{password}"
        f"@{host}:{port}/{database}"
    )

    return create_engine(database_url)


def apply_sql_schema():
    engine = get_engine()

    schema_path = (
        Path(__file__).resolve().parent.parent / "schema.sql"
    )

    sql_script = schema_path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(sql_script))

    print(
        "✓ SQL schema and views successfully created "
        "in PostgreSQL."
    )


if __name__ == "__main__":
    apply_sql_schema()