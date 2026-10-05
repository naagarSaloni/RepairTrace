from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.products import router as products_router
from app.routers.repairs import router as repairs_router
from app.routers.admin import router as admin_router
from app.routers.technician import router as technician_router
from app.routers.public import router as public_router
from app.routers.ownership import router as ownership_router
from app.routers.disputes import router as disputes_router
from app.routers.risk import router as risk_router
from app.routers.ai_risk import router as ai_risk_router
from app.routers.buyer import router as buyer_router

from app.db.database import (
    Base,
    engine,
    test_database_connection
)

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Serve uploaded files
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


# Register routers
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(repairs_router)
app.include_router(admin_router)
app.include_router(technician_router)
app.include_router(public_router)
app.include_router(ownership_router)
app.include_router(disputes_router)
app.include_router(risk_router)
app.include_router(ai_risk_router)
app.include_router(buyer_router)


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