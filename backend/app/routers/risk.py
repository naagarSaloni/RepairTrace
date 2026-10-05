from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Product
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.risk_analysis import calculate_trust_score


router = APIRouter(
    prefix="/api/risk",
    tags=["Risk Analysis"]
)


@router.get("/products/{product_uid}")
def analyze_product_risk(
    product_uid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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

    # Owner or admin can view detailed risk analysis.
    if (
        product.owner_id != current_user.id
        and current_user.role != "ADMIN"
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    result = calculate_trust_score(product, db)

    return {
        "product_uid": product.product_uid,
        "product_name": product.product_name,
        **result
    }