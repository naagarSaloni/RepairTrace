from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.products import router as products_router
from app.routers.repairs import router as repairs_router
from app.routers.admin import router as admin_router
from app.routers.technician import router as technician_router

from app.db.database import Base, engine, test_database_connection
from app.models import (
    User,
    Product,
    Repair,
    RepairPart,
    RepairHistory,
)

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="RepairTrace API",
    description="Blockchain-based repair tracking system",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(repairs_router)
app.include_router(admin_router)
app.include_router(technician_router)
@app.get("/")
def root():
    return {
        "message": "RepairTrace API is running"
    }


@app.get("/health")
def health():
    try:
        test_database_connection()

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }