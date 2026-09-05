import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Product
from app.models.repair import Repair
from app.models.user import User
from app.schemas.repair import RepairCreate, RepairResponse
from app.models.repair_history import RepairHistory
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/repairs",
    tags=["Repairs"]
)


@router.post(
    "/",
    response_model=RepairResponse
)
def create_repair(
    request: RepairCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = (
        db.query(Product)
        .filter(
            Product.id == request.product_id,
            Product.owner_id == current_user.id
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    repair_id = f"REP-{uuid.uuid4().hex[:10].upper()}"

    repair = Repair(
        repair_id=repair_id,
        product_id=product.id,
        customer_id=current_user.id,
        issue_description=request.issue_description,
        status="SUBMITTED"
    )

    db.add(repair)
    db.commit()
    db.refresh(repair)

    history = RepairHistory(
        repair_id=repair.id,
        status="SUBMITTED",
        description="Repair request submitted"
    )

    db.add(history)
    db.commit()

    return repair


@router.get(
    "/my-repairs",
    response_model=list[RepairResponse]
)
def get_my_repairs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Repair)
        .filter(Repair.customer_id == current_user.id)
        .order_by(Repair.created_at.desc())
        .all()
    )

@router.post("/{repair_id}/approve")
def approve_repair(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repair = (
        db.query(Repair)
        .filter(
            Repair.repair_id == repair_id,
            Repair.customer_id == current_user.id
        )
        .first()
    )

    if not repair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repair not found"
        )

    if repair.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repair cannot be approved from {repair.status}"
        )

    repair.status = "APPROVED"

    history = RepairHistory(
        repair_id=repair.id,
        status="APPROVED",
        description="Customer approved the diagnosis and repair"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Repair approved successfully",
        "repair_id": repair.repair_id,
        "status": repair.status
    }
@router.get(
    "/{repair_id}",
    response_model=RepairResponse
)
def get_repair(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repair = (
        db.query(Repair)
        .filter(
            Repair.repair_id == repair_id,
            Repair.customer_id == current_user.id
        )
        .first()
    )

    if not repair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repair not found"
        )

    return repair