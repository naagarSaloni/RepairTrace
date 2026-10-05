import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Product
from app.models.repair import Repair
from app.models.user import User
from app.models.repair_history import RepairHistory
from app.schemas.repair import RepairCreate, RepairResponse
from app.services.blockchain import verify_repair_hash
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/repairs",
    tags=["Repairs"]
)


# ==========================================================
# CREATE REPAIR
# ==========================================================

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

    if not request.issue_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Issue description cannot be empty"
        )

    repair_id = f"REP-{uuid.uuid4().hex[:10].upper()}"

    repair = Repair(
        repair_id=repair_id,
        product_id=product.id,
        customer_id=current_user.id,
        issue_description=request.issue_description.strip(),
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


# ==========================================================
# VERIFY REPAIR HASH
# ==========================================================

@router.get("/{repair_id}/verify-hash")
def verify_repair_record_hash(
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

    if not repair.record_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hash exists for this repair"
        )

    is_valid = verify_repair_hash(
        repair_id=repair.repair_id,
        product_id=repair.product_id,
        issue_description=repair.issue_description,
        diagnosis=repair.diagnosis,
        stored_hash=repair.record_hash
    )

    return {
        "repair_id": repair.repair_id,
        "stored_hash": repair.record_hash,
        "hash_valid": is_valid,
        "message": (
            "Repair record is authentic and unchanged"
            if is_valid
            else "Repair record has been modified"
        )
    }


# ==========================================================
# GET MY REPAIRS
# ==========================================================

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
        .filter(
            Repair.customer_id == current_user.id
        )
        .order_by(
            Repair.created_at.desc()
        )
        .all()
    )


# ==========================================================
# GET REPAIR HISTORY
# ==========================================================

@router.get(
    "/{repair_id}/history"
)
def get_repair_history(
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

    history = (
        db.query(RepairHistory)
        .filter(
            RepairHistory.repair_id == repair.id
        )
        .order_by(
            RepairHistory.created_at.asc()
        )
        .all()
    )

    return history


# ==========================================================
# GET SINGLE REPAIR
# ==========================================================

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


# ==========================================================
# CUSTOMER VERIFIES COMPLETED REPAIR
# ==========================================================

@router.post("/{repair_id}/verify")
def verify_completed_repair(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Customer verifies the completed repair.

    The repair must be COMPLETED and must have a
    SHA-256 record hash before customer verification.
    """

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

    if repair.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Repair cannot be verified from "
                f"{repair.status}. "
                f"Technician must complete the repair first."
            )
        )

    if not repair.record_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Repair cannot be verified because "
                "its SHA-256 record hash is missing"
            )
        )

    repair.status = "CUSTOMER_VERIFIED"

    history = RepairHistory(
        repair_id=repair.id,
        status="CUSTOMER_VERIFIED",
        description="Customer verified the completed repair"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Repair verified successfully",
        "repair_id": repair.repair_id,
        "status": repair.status,
        "record_hash": repair.record_hash
    }


# ==========================================================
# RETURN REPAIR
# ==========================================================

@router.post("/{repair_id}/return")
def return_repair(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Close the repair after customer verification.
    """

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

    if repair.status != "CUSTOMER_VERIFIED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Repair must be CUSTOMER_VERIFIED "
                "before it can be returned"
            )
        )

    repair.status = "RETURNED"

    history = RepairHistory(
        repair_id=repair.id,
        status="RETURNED",
        description="Product returned to customer and repair closed"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Repair returned and closed successfully",
        "repair_id": repair.repair_id,
        "status": repair.status,
        "record_hash": repair.record_hash
    }