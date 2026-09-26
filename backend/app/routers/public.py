from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Product


router = APIRouter(
    prefix="/api/public",
    tags=["Public Verification"]
)


@router.get("/products/{product_uid}")
def verify_product(
    product_uid: str,
    db: Session = Depends(get_db)
):
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

    return {
        "verified": True,
        "product_uid": product.product_uid,
        "product_name": product.product_name,
        "brand": product.brand,
        "model": product.model,
        "serial_number": product.serial_number,
        "message": "This product is registered in RepairTrace."
    }