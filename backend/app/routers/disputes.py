from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.repair import Repair
from app.models.dispute import Dispute
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/disputes",
    tags=["Disputes"]
)


# ============================================================
# CREATE DISPUTE
# ============================================================

@router.post("/repairs/{repair_id}")
def create_dispute(
    repair_id: str,
    reason: str,
    description: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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

    # Get the product explicitly because Repair does not
    # define a product relationship.
    product = (
        db.query(Product)
        .filter(Product.id == repair.product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product associated with this repair was not found"
        )

    # Only the current product owner can raise a dispute.
    if product.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the product owner can raise a dispute"
        )

    # Prevent multiple open disputes for the same repair.
    existing = (
        db.query(Dispute)
        .filter(
            Dispute.repair_id == repair.id,
            Dispute.status == "OPEN"
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="An open dispute already exists for this repair"
        )

    dispute = Dispute(
        repair_id=repair.id,
        raised_by=current_user.id,
        reason=reason,
        description=description,
        status="OPEN"
    )

    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    return {
        "message": "Dispute created successfully",
        "dispute_id": dispute.id,
        "repair_id": repair.repair_id,
        "reason": dispute.reason,
        "description": dispute.description,
        "status": dispute.status,
        "created_at": dispute.created_at
    }


# ============================================================
# GET MY DISPUTES
# ============================================================

@router.get("/my")
def get_my_disputes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    disputes = (
        db.query(Dispute)
        .filter(Dispute.raised_by == current_user.id)
        .order_by(Dispute.created_at.desc())
        .all()
    )

    return [
        {
            "id": dispute.id,
            "repair_id": dispute.repair_id,
            "reason": dispute.reason,
            "description": dispute.description,
            "status": dispute.status,
            "admin_response": dispute.admin_response,
            "created_at": dispute.created_at,
            "resolved_at": dispute.resolved_at
        }
        for dispute in disputes
    ]


# ============================================================
# GET ALL DISPUTES
# ============================================================

@router.get("/all")
def get_all_disputes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    disputes = (
        db.query(Dispute)
        .order_by(Dispute.created_at.desc())
        .all()
    )

    return [
        {
            "id": dispute.id,
            "repair_id": dispute.repair_id,
            "raised_by": dispute.raised_by,
            "reason": dispute.reason,
            "description": dispute.description,
            "status": dispute.status,
            "admin_response": dispute.admin_response,
            "created_at": dispute.created_at,
            "resolved_at": dispute.resolved_at,
            "resolved_by": dispute.resolved_by
        }
        for dispute in disputes
    ]


# ============================================================
# RESOLVE DISPUTE
# ============================================================

@router.patch("/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: int,
    admin_response: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    dispute = (
        db.query(Dispute)
        .filter(Dispute.id == dispute_id)
        .first()
    )

    if not dispute:
        raise HTTPException(
            status_code=404,
            detail="Dispute not found"
        )

    if dispute.status == "RESOLVED":
        raise HTTPException(
            status_code=400,
            detail="Dispute is already resolved"
        )

    dispute.status = "RESOLVED"
    dispute.admin_response = admin_response
    dispute.resolved_by = current_user.id
    dispute.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(dispute)

    return {
        "message": "Dispute resolved successfully",
        "dispute_id": dispute.id,
        "status": dispute.status,
        "admin_response": dispute.admin_response,
        "resolved_by": dispute.resolved_by,
        "resolved_at": dispute.resolved_at
    }