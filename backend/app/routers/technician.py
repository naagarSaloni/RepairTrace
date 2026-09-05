from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.repair import Repair
from app.models.repair_history import RepairHistory
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/technician",
    tags=["Technician"]
)


def check_technician(user: User):
    if user.role != "TECHNICIAN":
        raise HTTPException(
            status_code=403,
            detail="Technician access required"
        )


@router.get("/repairs")
def get_assigned_repairs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repairs = (
        db.query(Repair)
        .filter(
            Repair.technician_id == current_user.id
        )
        .order_by(Repair.created_at.desc())
        .all()
    )

    return repairs


@router.post("/repairs/{repair_id}/start-diagnosis")
def start_diagnosis(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = (
        db.query(Repair)
        .filter(
            Repair.repair_id == repair_id,
            Repair.technician_id == current_user.id
        )
        .first()
    )

    if not repair:
        raise HTTPException(
            status_code=404,
            detail="Assigned repair not found"
        )

    if repair.status != "RECEIVED":
        raise HTTPException(
            status_code=400,
            detail=f"Repair cannot start diagnosis from {repair.status}"
        )

    repair.status = "DIAGNOSING"

    history = RepairHistory(
        repair_id=repair.id,
        status="DIAGNOSING",
        description="Technician started diagnosis"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Diagnosis started",
        "repair_id": repair.repair_id,
        "status": repair.status
    }


@router.put("/repairs/{repair_id}/diagnosis")
def submit_diagnosis(
    repair_id: str,
    diagnosis: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = (
        db.query(Repair)
        .filter(
            Repair.repair_id == repair_id,
            Repair.technician_id == current_user.id
        )
        .first()
    )

    if not repair:
        raise HTTPException(
            status_code=404,
            detail="Assigned repair not found"
        )

    if repair.status != "DIAGNOSING":
        raise HTTPException(
            status_code=400,
            detail="Repair is not currently in diagnosis"
        )

    if not diagnosis.strip():
        raise HTTPException(
            status_code=400,
            detail="Diagnosis cannot be empty"
        )

    repair.diagnosis = diagnosis
    repair.status = "AWAITING_APPROVAL"

    history = RepairHistory(
        repair_id=repair.id,
        status="AWAITING_APPROVAL",
        description=f"Diagnosis submitted: {diagnosis}"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Diagnosis submitted successfully",
        "repair_id": repair.repair_id,
        "diagnosis": repair.diagnosis,
        "status": repair.status
    }