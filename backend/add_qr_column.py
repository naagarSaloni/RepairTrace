from sqlalchemy import text

from app.db.database import engine


with engine.begin() as connection:
    connection.execute(
        text(
            """
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS qr_code VARCHAR(500)
            """
        )
    )


print("qr_code column added successfully")