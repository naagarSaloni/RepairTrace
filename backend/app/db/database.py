from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured")

engine = create_engine(
    DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://"
    ),
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar()