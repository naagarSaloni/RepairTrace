from sqlalchemy import text

from app.db.database import engine


with engine.begin() as connection:
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS repair_documents (
                id SERIAL PRIMARY KEY,
                repair_id INTEGER NOT NULL
                    REFERENCES repairs(id),
                document_type VARCHAR(50) NOT NULL,
                file_name VARCHAR(255) NOT NULL,
                file_url VARCHAR(500) NOT NULL,
                description TEXT,
                uploaded_by INTEGER NOT NULL
                    REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


print("repair_documents table created successfully")