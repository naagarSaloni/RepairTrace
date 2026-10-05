from sqlalchemy import text
from app.db.database import engine

with engine.begin() as connection:
    connection.execute(
        text("ALTER TYPE repair_status ADD VALUE IF NOT EXISTS 'CUSTOMER_VERIFIED'")
    )

print("CUSTOMER_VERIFIED added successfully")