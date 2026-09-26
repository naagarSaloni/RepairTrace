import os
import uuid
import qrcode

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/products",
    tags=["Products"]
)


@router.post(
    "/",
    response_model=ProductResponse
)
def create_product(
    request: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product_uid = f"PRD-{uuid.uuid4().hex[:10].upper()}"

    # Create QR code containing the public verification URL
    verification_url = (
        f"http://127.0.0.1:8000/api/public/products/{product_uid}"
    )

    qr = qrcode.make(verification_url)

    # QR folder
    qr_folder = "uploads/qr"
    os.makedirs(qr_folder, exist_ok=True)

    # QR file name
    qr_filename = f"{product_uid}.png"
    qr_path = os.path.join(qr_folder, qr_filename)

    # Save QR image
    qr.save(qr_path)

    # Create product
    product = Product(
        product_uid=product_uid,
        owner_id=current_user.id,
        product_name=request.product_name,
        brand=request.brand,
        model=request.model,
        serial_number=request.serial_number,
        qr_code=f"/uploads/qr/{qr_filename}"
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get(
    "/my-products",
    response_model=list[ProductResponse]
)
def get_my_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Product)
        .filter(Product.owner_id == current_user.id)
        .all()
    )


@router.get(
    "/{product_uid}",
    response_model=ProductResponse
)
def get_product(
    product_uid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return (
        db.query(Product)
        .filter(
            Product.product_uid == product_uid,
            Product.owner_id == current_user.id
        )
        .first()
    )