from sqlalchemy import text

from app.database.connection import engine

with engine.connect() as connection:
    connection.execute(text("SELECT 1"))
    print("Database connection successful!")