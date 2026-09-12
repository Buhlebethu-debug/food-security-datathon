import os
from sqlalchemy import create_engine, text

def apply_sql_schema():
    # Database connection parameters
    db_user = os.getenv("USER", "postgres")
    db_pass = ""
    db_host = "localhost"
    db_port = "5432"
    db_name = "food_datathon"
    
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)
    
    # Read and execute schema.sql
    with open("schema.sql", "r") as f:
        sql_script = f.read()
        
    with engine.connect() as connection:
        connection.execute(text(sql_script))
        connection.commit()
        
    print("✓ SQL View 'view_eat_trade_empowerment_matrix' successfully created in PostgreSQL!")

if __name__ == "__main__":
    apply_sql_schema()