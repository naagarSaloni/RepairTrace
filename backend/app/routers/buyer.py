from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Product
from app.models.repair import Repair
from app.services.risk_analysis import calculate_trust_score
from app.services.blockchain import (
    verify_repair_hash,
    verify_repair_on_blockchain,
)


router = APIRouter(
    prefix="/api/buyer",
    tags=["Buyer Verification"]
)


@router.get("/products/{product_uid}/report")
def get_buyer_report(
    product_uid: str,
    db: Session = Depends(get_db),
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

    repairs = (
        db.query(Repair)
        .filter(Repair.product_id == product.id)
        .all()
    )

    risk = calculate_trust_score(product, db)

    repair_records = []

    for repair in repairs:
        hash_verified = False
        blockchain_verified = False

        if repair.record_hash:
            hash_verified = verify_repair_hash(
                repair_id=repair.repair_id,
                product_id=repair.product_id,
                issue_description=repair.issue_description,
                diagnosis=repair.diagnosis,
                stored_hash=repair.record_hash,
            )

            if hash_verified and repair.blockchain_tx_hash:
                blockchain_verified = verify_repair_on_blockchain(
                    repair_id=repair.repair_id,
                    record_hash=repair.record_hash,
                )

        repair_records.append({
            "repair_id": repair.repair_id,
            "issue_description": repair.issue_description,
            "diagnosis": repair.diagnosis,
            "status": repair.status,
            "record_hash": repair.record_hash,
            "hash_verified": hash_verified,
            "blockchain_tx_hash": repair.blockchain_tx_hash,
            "blockchain_verified": blockchain_verified,
        })

    completed_repairs = [
        repair
        for repair in repairs
        if repair.status in {
            "COMPLETED",
            "RETURNED",
            "CUSTOMER_VERIFIED",
        }
    ]

    blockchain_verified_count = sum(
        1
        for repair in repair_records
        if repair["blockchain_verified"]
    )

    hash_verified_count = sum(
        1
        for repair in repair_records
        if repair["hash_verified"]
    )

    return {
        "verified": True,
        "report_type": "Buyer Product Verification Report",

        "product": {
            "product_uid": product.product_uid,
            "product_name": product.product_name,
            "brand": product.brand,
            "model": product.model,
            "serial_number": product.serial_number,
        },

        "trust": {
            "trust_score": risk["trust_score"],
            "risk_level": risk["risk_level"],
            "risk_flags": risk["risk_flags"],
        },

        "repair_summary": {
            "total_repairs": len(repairs),
            "completed_repairs": len(completed_repairs),
            "hash_verified_repairs": hash_verified_count,
            "blockchain_verified_repairs": blockchain_verified_count,
        },

        "repairs": repair_records,

        "buyer_recommendation": (
            "Product history appears relatively trustworthy."
            if risk["trust_score"] >= 80
            else
            "Review repair history and supporting documents carefully "
            "before purchasing this product."
        ),
    }