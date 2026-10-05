from pathlib import Path
import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Product
from app.models.repair import Repair
from app.models.repair_part import RepairPart
from app.models.repair_document import RepairDocument
from app.models.repair_history import RepairHistory

from app.services.blockchain import (
    verify_repair_hash,
    verify_repair_on_blockchain,
)

from app.services.risk_analysis import calculate_trust_score


router = APIRouter(
    prefix="/api/public",
    tags=["Public Verification"]
)


# ============================================================
# PUBLIC PRODUCT PASSPORT / QR VERIFICATION
# ============================================================

@router.get("/products/{product_uid}")
def verify_product(
    product_uid: str,
    db: Session = Depends(get_db)
):
    """
    Public Product Passport.

    This endpoint can be accessed using the product QR code
    without requiring authentication.

    It provides:
    - Product information
    - Repair history
    - Component history
    - Repair documents
    - SHA-256 verification
    - Blockchain verification
    - Trust score
    """

    # --------------------------------------------------------
    # 1. Find product
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
    # 2. Find all repairs
    # --------------------------------------------------------

    repairs = (
        db.query(Repair)
        .filter(Repair.product_id == product.id)
        .order_by(Repair.created_at.asc())
        .all()
    )

    repair_list = []

    # Number of actually verified blockchain repairs
    blockchain_verified_count = 0

    # Number of repairs whose stored hash is valid
    hash_verified_count = 0

    # --------------------------------------------------------
    # 3. Build repair history
    # --------------------------------------------------------

    for repair in repairs:

        # ----------------------------------------------------
        # Components
        # ----------------------------------------------------

        parts = (
            db.query(RepairPart)
            .filter(
                RepairPart.repair_id == repair.id
            )
            .all()
        )

        part_list = []

        for part in parts:
            part_list.append({
                "part_name": part.part_name,
                "old_part_serial": part.old_part_serial,
                "new_part_serial": part.new_part_serial,
                "warranty_months": part.warranty_months,
                "replaced_at": (
                    part.replaced_at.isoformat()
                    if part.replaced_at
                    else None
                )
            })

        # ----------------------------------------------------
        # Documents
        # ----------------------------------------------------

        documents = (
            db.query(RepairDocument)
            .filter(
                RepairDocument.repair_id == repair.id
            )
            .all()
        )

        document_list = []

        for document in documents:
            document_list.append({
                "id": document.id,
                "document_type": document.document_type,
                "file_name": document.file_name,
                "file_url": document.file_url,

                # SHA-256 document proof
                "file_hash": document.file_hash,

                "description": document.description,

                "uploaded_at": (
                    document.created_at.isoformat()
                    if document.created_at
                    else None
                )
            })

        # ----------------------------------------------------
        # Repair status history
        # ----------------------------------------------------

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

        history_list = []

        for item in history:
            history_list.append({
                "status": item.status,
                "description": item.description,

                "created_at": (
                    item.created_at.isoformat()
                    if item.created_at
                    else None
                ),

                "blockchain_tx_hash": item.blockchain_tx_hash
            })

        # ----------------------------------------------------
        # SHA-256 repair verification
        # ----------------------------------------------------

        hash_verified = False

        if repair.record_hash:
            try:
                hash_verified = verify_repair_hash(
                    repair_id=repair.repair_id,
                    product_id=repair.product_id,
                    issue_description=repair.issue_description,
                    diagnosis=repair.diagnosis,
                    stored_hash=repair.record_hash
                )
            except Exception:
                hash_verified = False

        if hash_verified:
            hash_verified_count += 1

        # ----------------------------------------------------
        # ACTUAL blockchain verification
        # ----------------------------------------------------

        blockchain_verified = False

        if (
            repair.blockchain_tx_hash
            and repair.record_hash
            and hash_verified
        ):
            blockchain_verified = verify_repair_on_blockchain(
                repair_id=repair.repair_id,
                record_hash=repair.record_hash
            )

        if blockchain_verified:
            blockchain_verified_count += 1

        # ----------------------------------------------------
        # Repair verification status
        # ----------------------------------------------------

        if blockchain_verified:
            verification_status = "BLOCKCHAIN_VERIFIED"

        elif hash_verified:
            verification_status = "HASH_VERIFIED"

        elif repair.record_hash:
            verification_status = "VERIFICATION_FAILED"

        else:
            verification_status = "NOT_VERIFIED"

        # ----------------------------------------------------
        # Add repair to public history
        # ----------------------------------------------------

        repair_list.append({
            "repair_id": repair.repair_id,

            "issue_description": repair.issue_description,

            "diagnosis": repair.diagnosis,

            "status": repair.status,

            "created_at": (
                repair.created_at.isoformat()
                if repair.created_at
                else None
            ),

            "updated_at": (
                repair.updated_at.isoformat()
                if repair.updated_at
                else None
            ),

            # ------------------------------------------------
            # SHA-256 proof
            # ------------------------------------------------

            "record_hash": repair.record_hash,

            "hash_verified": hash_verified,

            # ------------------------------------------------
            # Blockchain proof
            # ------------------------------------------------

            "blockchain_tx_hash": repair.blockchain_tx_hash,

            "blockchain_verified": blockchain_verified,

            "verification_status": verification_status,

            # ------------------------------------------------
            # Components
            # ------------------------------------------------

            "components": part_list,

            # ------------------------------------------------
            # Documents
            # ------------------------------------------------

            "documents": document_list,

            # ------------------------------------------------
            # Status history
            # ------------------------------------------------

            "status_history": history_list
        })

    # --------------------------------------------------------
    # 4. Product-level summary
    # --------------------------------------------------------

    completed_repairs = [
        repair
        for repair in repairs
        if repair.status in {
            "COMPLETED",
            "CUSTOMER_VERIFIED",
            "RETURNED"
        }
    ]

    # --------------------------------------------------------
    # Cancelled repairs
    # --------------------------------------------------------

    cancelled_repairs = [
        repair
        for repair in repairs
        if repair.status == "CANCELLED"
    ]

    # --------------------------------------------------------
    # 5. Product trust score
    # --------------------------------------------------------

    trust_score_result = calculate_trust_score(
        product,
        db
    )

    trust_score = trust_score_result.get(
        "trust_score",
        100
    )

    risk_level = trust_score_result.get(
        "risk_level"
    )

    risk_flags = trust_score_result.get(
        "risk_flags",
        []
    )

    # --------------------------------------------------------
    # 6. Final Product Passport
    # --------------------------------------------------------

    return {
        "verified": True,

        "passport": {
            "product_uid": product.product_uid,
            "product_name": product.product_name,
            "brand": product.brand,
            "model": product.model,
            "serial_number": product.serial_number
        },

        "summary": {
            "total_repairs": len(repairs),

            "completed_repairs": len(
                completed_repairs
            ),

            "hash_verified_repairs": (
                hash_verified_count
            ),

            "blockchain_verified_repairs": (
                blockchain_verified_count
            ),

            "cancelled_repairs": len(
                cancelled_repairs
            ),

            "trust_score": trust_score,

            "risk_level": risk_level,

            "risk_flags": risk_flags
        },

        "repair_history": repair_list,

        "message": (
            "This product is registered in RepairTrace. "
            "Repair records are verified using SHA-256 "
            "cryptographic hashes and, where available, "
            "the RepairTrace blockchain record."
        )
    }


# ============================================================
# DOCUMENT SHA-256 VERIFICATION
# ============================================================

@router.get("/documents/{document_id}/verify")
def verify_document_hash(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    Verify whether a stored repair document has been modified.

    The SHA-256 hash calculated from the current file is
    compared with the hash stored when the document was uploaded.
    """

    document = (
        db.query(RepairDocument)
        .filter(
            RepairDocument.id == document_id
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # --------------------------------------------------------
    # No stored hash
    # --------------------------------------------------------

    if not document.file_hash:
        return {
            "verified": False,

            "document_id": document.id,

            "file_name": document.file_name,

            "stored_hash": None,

            "current_hash": None,

            "message": (
                "This document does not have a stored "
                "SHA-256 hash. Upload the document again "
                "to generate its hash."
            )
        }

    # --------------------------------------------------------
    # Convert URL to local path
    # --------------------------------------------------------

    file_path = Path(
        document.file_url.lstrip("/")
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document file not found on server"
        )

    # --------------------------------------------------------
    # Calculate current SHA-256
    # --------------------------------------------------------

    sha256 = hashlib.sha256()

    try:
        with file_path.open("rb") as file:
            while True:
                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                sha256.update(chunk)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not calculate document hash: {str(exc)}"
        )

    current_hash = sha256.hexdigest()

    # --------------------------------------------------------
    # Compare hashes
    # --------------------------------------------------------

    verified = (
        current_hash == document.file_hash
    )

    return {
        "verified": verified,

        "document_id": document.id,

        "file_name": document.file_name,

        "stored_hash": document.file_hash,

        "current_hash": current_hash,

        "message": (
            "Document integrity verified. "
            "The current file matches the stored SHA-256 hash."
            if verified
            else
            "Document integrity verification failed. "
            "The current file does not match the stored SHA-256 hash."
        )
    }


# ============================================================
# PUBLIC PRODUCT RISK
# ============================================================

@router.get("/products/{product_uid}/risk")
def public_product_risk(
    product_uid: str,
    db: Session = Depends(get_db),
):
    """
    Public risk/trust analysis for a product.
    """

    product = (
        db.query(Product)
        .filter(
            Product.product_uid == product_uid
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    result = calculate_trust_score(
        product,
        db
    )

    return {
        "product_uid": product.product_uid,

        "trust_score": result.get(
            "trust_score",
            0
        ),

        "risk_level": result.get(
            "risk_level"
        ),

        "risk_flags": result.get(
            "risk_flags",
            []
        ),

        "total_repairs": result.get(
            "total_repairs",
            0
        )
    }