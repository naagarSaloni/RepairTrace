from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Product
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.ai_risk import generate_ai_risk_analysis


router = APIRouter(
    prefix="/api/ai-risk",
    tags=["AI Risk Analysis"]
)


@router.get("/products/{product_uid}")
def analyze_product_with_ai(
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

    if (
        product.owner_id != current_user.id
        and current_user.role != "ADMIN"
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    analysis = generate_ai_risk_analysis(product, db)

    return {
        "product_uid": product.product_uid,
        "product_name": product.product_name,
        "analysis_type": "AI-assisted risk analysis",
        **analysis
    }