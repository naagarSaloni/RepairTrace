from pathlib import Path
import uuid
import hashlib

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
)

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.repair import Repair
from app.models.repair_part import RepairPart
from app.models.repair_history import RepairHistory
from app.models.repair_document import RepairDocument

from app.core.dependencies import get_current_user

from app.services.blockchain import (
    generate_repair_hash,
    add_repair_to_blockchain,
)

from app.services.document_extraction import (
    extract_document_text,
)

from app.services.fraud_detection import (
    check_component_product_mismatch,
    check_document_content,
)


router = APIRouter(
    prefix="/api/technician",
    tags=["Technician"],
)


# =========================================================
# DOCUMENT CONFIGURATION
# =========================================================

DOCUMENT_FOLDER = Path("uploads/documents")

DOCUMENT_FOLDER.mkdir(
    parents=True,
    exist_ok=True,
)


ALLOWED_DOCUMENT_TYPES = {
    "INVOICE",
    "WARRANTY",
    "REPAIR_REPORT",
    "BEFORE_PHOTO",
    "AFTER_PHOTO",
    "OTHER",
}


# Only formats currently supported by document_extraction.py.
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


# =========================================================
# TECHNICIAN CHECK
# =========================================================

def check_technician(user: User):
    if user.role != "TECHNICIAN":
        raise HTTPException(
            status_code=403,
            detail="Technician access required",
        )

    return user


# =========================================================
# GET TECHNICIAN REPAIR
# =========================================================

def get_technician_repair(
    repair_id: str,
    db: Session,
    current_user: User,
):
    repair = (
        db.query(Repair)
        .filter(
            Repair.repair_id == repair_id,
            Repair.technician_id == current_user.id,
        )
        .first()
    )

    if not repair:
        raise HTTPException(
            status_code=404,
            detail="Repair not found or not assigned to you",
        )

    return repair


# =========================================================
# GET TECHNICIAN REPAIRS
# =========================================================

@router.get("/repairs")
def get_technician_repairs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_technician(current_user)

    return (
        db.query(Repair)
        .filter(
            Repair.technician_id == current_user.id
        )
        .order_by(
            Repair.created_at.desc()
        )
        .all()
    )


# =========================================================
# START DIAGNOSIS
# =========================================================

@router.post("/repairs/{repair_id}/start-diagnosis")
def start_diagnosis(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user,
    )

    if repair.status != "RECEIVED":
        raise HTTPException(
            status_code=400,
            detail="Repair must be RECEIVED before diagnosis",
        )

    repair.status = "DIAGNOSING"

    history = RepairHistory(
        repair_id=repair.id,
        status="DIAGNOSING",
        description="Technician started diagnosis",
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Diagnosis started",
        "repair_id": repair.repair_id,
        "status": repair.status,
    }


# =========================================================
# UPDATE DIAGNOSIS
# =========================================================

@router.put("/repairs/{repair_id}/diagnosis")
def update_diagnosis(
    repair_id: str,
    diagnosis: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user,
    )

    if repair.status != "DIAGNOSING":
        raise HTTPException(
            status_code=400,
            detail="Repair is not currently in diagnosis",
        )

    if not diagnosis.strip():
        raise HTTPException(
            status_code=400,
            detail="Diagnosis cannot be empty",
        )

    repair.diagnosis = diagnosis.strip()

    history = RepairHistory(
        repair_id=repair.id,
        status="DIAGNOSING",
        description=f"Diagnosis updated: {repair.diagnosis}",
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Diagnosis updated successfully",
        "repair_id": repair.repair_id,
        "diagnosis": repair.diagnosis,
        "status": repair.status,
    }


# =========================================================
# START REPAIR
# =========================================================

@router.post("/repairs/{repair_id}/start-repair")
def start_repair(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user,
    )

    if repair.status != "DIAGNOSING":
        raise HTTPException(
            status_code=400,
            detail="Diagnosis must be completed before repair",
        )

    if not repair.diagnosis or not repair.diagnosis.strip():
        raise HTTPException(
            status_code=400,
            detail="Diagnosis is required before starting repair",
        )

    repair.status = "IN_REPAIR"

    history = RepairHistory(
        repair_id=repair.id,
        status="IN_REPAIR",
        description="Technician started repair",
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Repair started",
        "repair_id": repair.repair_id,
        "status": repair.status,
    }


# =========================================================
# ADD REPAIR PART
# =========================================================

@router.post("/repairs/{repair_id}/parts")
def add_repair_part(
    repair_id: str,
    part_name: str = Form(...),
    old_part_serial: str | None = Form(None),
    new_part_serial: str | None = Form(None),
    warranty_months: int = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user,
    )

    if repair.status not in {
        "IN_REPAIR",
        "PART_REPLACED",
    }:
        raise HTTPException(
            status_code=400,
            detail="Parts can only be added during repair",
        )

    if not part_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Part name cannot be empty",
        )

    if warranty_months < 0:
        raise HTTPException(
            status_code=400,
            detail="Warranty months cannot be negative",
        )

    fraud_flags = []

    # =====================================================
    # FRAUD CHECK 1 — DUPLICATE COMPONENT SERIAL
    # =====================================================

    if new_part_serial and new_part_serial.strip():
        cleaned_serial = new_part_serial.strip()

        existing_part = (
            db.query(RepairPart)
            .filter(
                RepairPart.new_part_serial == cleaned_serial
            )
            .first()
        )

        if existing_part:
            fraud_flags.append({
                "type": "DUPLICATE_COMPONENT_SERIAL",
                "severity": "HIGH",
                "message": (
                    f"Component serial '{cleaned_serial}' "
                    f"is already associated with another repair."
                ),
            })

    # =====================================================
    # FRAUD CHECK 2 — COMPONENT / PRODUCT MISMATCH
    # =====================================================

    product = (
        db.query(Product)
        .filter(
            Product.id == repair.product_id
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product associated with this repair was not found",
        )

    mismatch_result = check_component_product_mismatch(
        product_name=product.product_name,
        product_brand=product.brand,
        product_model=product.model,
        part_name=part_name,
    )

    if mismatch_result["fraud_detected"]:
        fraud_flags.append({
            "type": "COMPONENT_PRODUCT_MISMATCH",
            "severity": mismatch_result["severity"],
            "message": mismatch_result["flag"],
        })

    # =====================================================
    # CREATE COMPONENT RECORD
    # =====================================================

    part = RepairPart(
        repair_id=repair.id,
        part_name=part_name.strip(),
        old_part_serial=(
            old_part_serial.strip()
            if old_part_serial and old_part_serial.strip()
            else None
        ),
        new_part_serial=(
            new_part_serial.strip()
            if new_part_serial and new_part_serial.strip()
            else None
        ),
        warranty_months=warranty_months,
    )

    db.add(part)
    db.commit()
    db.refresh(part)

    return {
        "message": "Repair part added",
        "part_id": part.id,
        "part_name": part.part_name,
        "new_part_serial": part.new_part_serial,
        "fraud_detected": bool(fraud_flags),
        "fraud_flags": fraud_flags,
    }


# =========================================================
# GET REPAIR PARTS
# =========================================================

@router.get("/repairs/{repair_id}/parts")
def get_repair_parts(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user,
    )

    return (
        db.query(RepairPart)
        .filter(
            RepairPart.repair_id == repair.id
        )
        .order_by(
            RepairPart.replaced_at.asc()
        )
        .all()
    )


# =========================================================
# MARK PART REPLACED
# =========================================================

@router.post("/repairs/{repair_id}/part-replaced")
def mark_part_replaced(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user,
    )

    if repair.status != "IN_REPAIR":
        raise HTTPException(
            status_code=400,
            detail="Repair must be IN_REPAIR",
        )

    parts = (
        db.query(RepairPart)
        .filter(
            RepairPart.repair_id == repair.id
        )
        .all()
    )

    if not parts:
        raise HTTPException(
            status_code=400,
            detail="No repair parts have been added",
        )

    repair.status = "PART_REPLACED"

    history = RepairHistory(
        repair_id=repair.id,
        status="PART_REPLACED",
        description="Replacement parts recorded",
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Parts marked as replaced",
        "repair_id": repair.repair_id,
        "status": repair.status,
    }


# =========================================================
# UPLOAD REPAIR DOCUMENT
# =========================================================

@router.post("/repairs/{repair_id}/documents")
def upload_repair_document(
    repair_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user,
    )

    document_type = document_type.upper().strip()

    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid document type",
        )

    extension = Path(
        file.filename or ""
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "File type not allowed. "
                "Supported formats: PDF, PNG, JPG, JPEG and WEBP."
            ),
        )

    if repair.status not in {
        "DIAGNOSING",
        "IN_REPAIR",
        "PART_REPLACED",
        "COMPLETED",
    }:
        raise HTTPException(
            status_code=400,
            detail="Documents cannot be uploaded at this stage",
        )

    # =====================================================
    # GET PRODUCT
    # =====================================================

    product = (
        db.query(Product)
        .filter(
            Product.id == repair.product_id
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product associated with this repair was not found",
        )

    # =====================================================
    # SAVE FILE + CALCULATE SHA-256
    # =====================================================

    unique_name = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = DOCUMENT_FOLDER / unique_name

    sha256 = hashlib.sha256()

    try:
        with file_path.open("wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                buffer.write(chunk)
                sha256.update(chunk)

    except Exception as exc:
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save document: {str(exc)}",
        )

    file_hash = sha256.hexdigest()

    file_url = (
        f"/uploads/documents/{unique_name}"
    )

    # =====================================================
    # EXTRACT DOCUMENT CONTENT
    # =====================================================

    extracted_text = ""

    if document_type in {
        "INVOICE",
        "WARRANTY",
        "REPAIR_REPORT",
        "OTHER",
    }:
        extracted_text = extract_document_text(
            file_path
        )

    # =====================================================
    # FRAUD DETECTION
    # =====================================================

    fraud_flags = []
    fraud_detected = False
    fraud_severity = "LOW"

    if extracted_text:
        product_validation = check_document_content(
            document_text=extracted_text,
            product_name=product.product_name,
            product_brand=product.brand,
            product_model=product.model,
        )

        if product_validation["fraud_detected"]:
            fraud_detected = True

        if product_validation["severity"] == "HIGH":
            fraud_severity = "HIGH"

        elif (
            product_validation["severity"] == "MEDIUM"
            and fraud_severity != "HIGH"
        ):
            fraud_severity = "MEDIUM"

        fraud_flags.extend(
            product_validation["flags"]
        )

        # -------------------------------------------------
        # COMPONENT CONTENT VALIDATION
        # -------------------------------------------------

        repair_parts = (
            db.query(RepairPart)
            .filter(
                RepairPart.repair_id == repair.id
            )
            .all()
        )

        for part in repair_parts:
            part_validation = check_document_content(
                document_text=extracted_text,
                product_name=product.product_name,
                product_brand=product.brand,
                product_model=product.model,
                part_name=part.part_name,
                part_serial=part.new_part_serial,
            )

            if part_validation["fraud_detected"]:
                fraud_detected = True

            if part_validation["severity"] == "HIGH":
                fraud_severity = "HIGH"

            elif (
                part_validation["severity"] == "MEDIUM"
                and fraud_severity != "HIGH"
            ):
                fraud_severity = "MEDIUM"

            fraud_flags.extend(
                part_validation["flags"]
            )

    # =====================================================
    # CREATE DOCUMENT RECORD
    # =====================================================

    document = RepairDocument(
        repair_id=repair.id,
        document_type=document_type,
        file_name=file.filename or unique_name,
        file_url=file_url,
        file_hash=file_hash,
        description=description.strip() if description else None,
        uploaded_by=current_user.id,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "message": "Document uploaded successfully",
        "document_id": document.id,
        "document_type": document.document_type,
        "file_name": document.file_name,
        "file_url": document.file_url,
        "file_hash": document.file_hash,
        "content_validation": {
            "performed": bool(extracted_text),
            "text_length": len(extracted_text),
            "fraud_detected": fraud_detected,
            "severity": fraud_severity,
            "fraud_flags": fraud_flags,
        },
    }


# =========================================================
# GET REPAIR DOCUMENTS
# =========================================================

@router.get("/repairs/{repair_id}/documents")
def get_repair_documents(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user,
    )

    return (
        db.query(RepairDocument)
        .filter(
            RepairDocument.repair_id == repair.id
        )
        .order_by(
            RepairDocument.created_at.desc()
        )
        .all()
    )


# =========================================================
# COMPLETE REPAIR
# =========================================================

@router.post("/repairs/{repair_id}/complete")
def complete_repair(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user,
    )

    # =====================================================
    # STATUS VALIDATION
    # =====================================================

    if repair.status not in {
        "IN_REPAIR",
        "PART_REPLACED",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Repair must be IN_REPAIR or PART_REPLACED "
                "before completion"
            ),
        )

    if not repair.diagnosis or not repair.diagnosis.strip():
        raise HTTPException(
            status_code=400,
            detail="Diagnosis is required before completing repair",
        )

    # =====================================================
    # GENERATE SHA-256 REPAIR HASH
    # =====================================================

    repair_hash = generate_repair_hash(
        repair_id=repair.repair_id,
        product_id=repair.product_id,
        issue_description=repair.issue_description,
        diagnosis=repair.diagnosis,
    )

    # =====================================================
    # STORE REPAIR ON BLOCKCHAIN
    # =====================================================

    try:
        tx_hash = add_repair_to_blockchain(
            repair_id=repair.repair_id,
            record_hash=repair_hash,
        )
    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=503,
            detail=(
                "Repair cannot be completed because the "
                f"blockchain record could not be created: {str(exc)}"
            ),
        )

    # =====================================================
    # UPDATE REPAIR
    # =====================================================

    repair.status = "COMPLETED"
    repair.record_hash = repair_hash
    repair.blockchain_tx_hash = tx_hash

    # =====================================================
    # REPAIR HISTORY
    # =====================================================

    history = RepairHistory(
        repair_id=repair.id,
        status="COMPLETED",
        description="Technician completed the repair",
    )

    db.add(history)

    try:
        db.commit()
        db.refresh(repair)
    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Repair completion could not be saved",
        )

    # =====================================================
    # RESPONSE
    # =====================================================

    return {
        "message": "Repair completed successfully",
        "repair_id": repair.repair_id,
        "status": repair.status,
        "record_hash": repair.record_hash,
        "blockchain_tx_hash": repair.blockchain_tx_hash,
    }