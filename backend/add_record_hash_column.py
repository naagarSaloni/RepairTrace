from sqlalchemy import text

from app.db.database import engine


with engine.begin() as connection:
    connection.execute(
        text("""
            ALTER TABLE repairs
            ADD COLUMN IF NOT EXISTS record_hash VARCHAR(255)
        """)
    )

print("record_hash column added successfully")