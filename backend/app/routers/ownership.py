from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.product import Product
from app.models.user import User
from app.models.ownership_history import OwnershipHistory


router = APIRouter(
    prefix="/api/ownership",
    tags=["Ownership"]
)


# ============================================================
# TRANSFER OWNERSHIP
# ============================================================

@router.post("/transfer")
def transfer_ownership(
    product_uid: str,
    new_owner_email: str,
    transfer_reason: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # --------------------------------------------------------
    # Find product
    # --------------------------------------------------------

    product = (
        db.query(Product)
        .filter(Product.product_uid == product_uid)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # --------------------------------------------------------
    # Only current owner can transfer
    # --------------------------------------------------------

    if product.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the current owner can transfer ownership"
        )

    # --------------------------------------------------------
    # Find new owner
    # --------------------------------------------------------

    new_owner = (
        db.query(User)
        .filter(User.email == new_owner_email.strip().lower())
        .first()
    )

    if not new_owner:
        raise HTTPException(
            status_code=404,
            detail="New owner not found"
        )

    # --------------------------------------------------------
    # Prevent self-transfer
    # --------------------------------------------------------

    if new_owner.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Product is already owned by this user"
        )

    # --------------------------------------------------------
    # Only customers can become product owners
    # --------------------------------------------------------

    if new_owner.role != "CUSTOMER":
        raise HTTPException(
            status_code=400,
            detail="Product ownership can only be transferred to a customer"
        )

    # --------------------------------------------------------
    # Store previous owner
    # --------------------------------------------------------

    previous_owner_id = product.owner_id

    # --------------------------------------------------------
    # Create ownership history
    # --------------------------------------------------------

    history = OwnershipHistory(
        product_id=product.id,
        previous_owner_id=previous_owner_id,
        new_owner_id=new_owner.id,
        transfer_reason=transfer_reason
    )

    # --------------------------------------------------------
    # Update product owner
    # --------------------------------------------------------

    product.owner_id = new_owner.id

    db.add(history)

    try:
        db.commit()
        db.refresh(product)
        db.refresh(history)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to transfer product ownership"
        )

    return {
        "message": "Product ownership transferred successfully",
        "product_uid": product.product_uid,
        "previous_owner_id": previous_owner_id,
        "new_owner_id": new_owner.id,
        "new_owner_name": new_owner.name,
        "new_owner_email": new_owner.email,
        "transfer_reason": transfer_reason,
        "transferred_at": history.transferred_at
    }


# ============================================================
# GET OWNERSHIP HISTORY
# ============================================================

@router.get("/{product_uid}/history")
def get_ownership_history(
    product_uid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # --------------------------------------------------------
    # Find product
    # --------------------------------------------------------

    product = (
        db.query(Product)
        .filter(Product.product_uid == product_uid)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # --------------------------------------------------------
    # Only current owner can view private ownership history
    # --------------------------------------------------------

    if product.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not the current owner of this product"
        )

    # --------------------------------------------------------
    # Get history
    # --------------------------------------------------------

    history = (
        db.query(OwnershipHistory)
        .filter(
            OwnershipHistory.product_id == product.id
        )
        .order_by(
            OwnershipHistory.transferred_at.asc()
        )
        .all()
    )

    result = []

    for record in history:

        previous_owner = (
            db.query(User)
            .filter(User.id == record.previous_owner_id)
            .first()
        )

        new_owner = (
            db.query(User)
            .filter(User.id == record.new_owner_id)
            .first()
        )

        result.append({
            "id": record.id,

            "previous_owner": {
                "id": previous_owner.id if previous_owner else None,
                "name": previous_owner.name if previous_owner else None,
                "email": previous_owner.email if previous_owner else None
            },

            "new_owner": {
                "id": new_owner.id if new_owner else None,
                "name": new_owner.name if new_owner else None,
                "email": new_owner.email if new_owner else None
            },

            "transfer_reason": record.transfer_reason,

            "blockchain_tx_hash": record.blockchain_tx_hash,

            "transferred_at": record.transferred_at
        })

    return {
        "product_uid": product_uid,
        "current_owner_id": product.owner_id,
        "ownership_transfers": result
    }