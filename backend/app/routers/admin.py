from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.repair import Repair
from app.models.repair_history import RepairHistory
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


@router.get("/technicians")
def get_technicians(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    technicians = (
        db.query(User)
        .filter(User.role == "TECHNICIAN")
        .all()
    )

    return [
        {
            "id": technician.id,
            "name": technician.name,
            "email": technician.email
        }
        for technician in technicians
    ]


@router.post("/repairs/{repair_id}/assign/{technician_id}")
def assign_technician(
    repair_id: str,
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    repair = (
        db.query(Repair)
        .filter(Repair.repair_id == repair_id)
        .first()
    )

    if not repair:
        raise HTTPException(
            status_code=404,
            detail="Repair not found"
        )

    technician = (
        db.query(User)
        .filter(
            User.id == technician_id,
            User.role == "TECHNICIAN"
        )
        .first()
    )

    if not technician:
        raise HTTPException(
            status_code=404,
            detail="Technician not found"
        )

    repair.technician_id = technician.id
    repair.status = "RECEIVED"

    history = RepairHistory(
        repair_id=repair.id,
        status="RECEIVED",
        description=f"Technician {technician.name} assigned"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Technician assigned successfully",
        "repair_id": repair.repair_id,
        "technician_id": technician.id,
        "status": repair.status
    }