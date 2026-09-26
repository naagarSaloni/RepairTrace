from pathlib import Path
import shutil
import uuid

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
from app.models.repair import Repair
from app.models.repair_part import RepairPart
from app.models.repair_history import RepairHistory
from app.models.repair_document import RepairDocument
from app.core.dependencies import get_current_user
from app.services.blockchain import generate_repair_hash


router = APIRouter(
    prefix="/api/technician",
    tags=["Technician"]
)


DOCUMENT_FOLDER = Path("uploads/documents")

DOCUMENT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

ALLOWED_DOCUMENT_TYPES = {
    "INVOICE",
    "WARRANTY",
    "REPAIR_REPORT",
    "BEFORE_PHOTO",
    "AFTER_PHOTO",
    "OTHER"
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx"
}


def check_technician(user: User):
    if user.role != "TECHNICIAN":
        raise HTTPException(
            status_code=403,
            detail="Technician access required"
        )
    return user


def get_technician_repair(
    repair_id: str,
    db: Session,
    current_user: User
):
    repair = (
        db.query(Repair)
        .filter(
            Repair.repair_id == repair_id,
            Repair.technician_id == current_user.id
        )
        .first()
    )

    if not repair:
        raise HTTPException(
            status_code=404,
            detail="Repair not found or not assigned to you"
        )

    return repair


@router.get("/repairs")
def get_technician_repairs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repairs = (
        db.query(Repair)
        .filter(
            Repair.technician_id == current_user.id
        )
        .order_by(
            Repair.created_at.desc()
        )
        .all()
    )

    return repairs


@router.post("/repairs/{repair_id}/start-diagnosis")
def start_diagnosis(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user
    )

    if repair.status != "RECEIVED":
        raise HTTPException(
            status_code=400,
            detail="Repair must be RECEIVED before diagnosis"
        )

    repair.status = "DIAGNOSING"

    history = RepairHistory(
        repair_id=repair.id,
        status="DIAGNOSING",
        description="Technician started diagnosis"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Diagnosis started",
        "repair_id": repair.repair_id,
        "status": repair.status
    }


@router.put("/repairs/{repair_id}/diagnosis")
def update_diagnosis(
    repair_id: str,
    diagnosis: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user
    )

    if repair.status != "DIAGNOSING":
        raise HTTPException(
            status_code=400,
            detail="Repair is not currently in diagnosis"
        )

    if not diagnosis.strip():
        raise HTTPException(
            status_code=400,
            detail="Diagnosis cannot be empty"
        )

    repair.diagnosis = diagnosis.strip()

    history = RepairHistory(
        repair_id=repair.id,
        status="DIAGNOSING",
        description=f"Diagnosis updated: {repair.diagnosis}"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Diagnosis updated successfully",
        "repair_id": repair.repair_id,
        "diagnosis": repair.diagnosis,
        "status": repair.status
    }


@router.post("/repairs/{repair_id}/start-repair")
def start_repair(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user
    )

    if repair.status != "DIAGNOSING":
        raise HTTPException(
            status_code=400,
            detail="Diagnosis must be completed before repair"
        )

    if not repair.diagnosis:
        raise HTTPException(
            status_code=400,
            detail="Diagnosis is required before starting repair"
        )

    repair.status = "IN_REPAIR"

    history = RepairHistory(
        repair_id=repair.id,
        status="IN_REPAIR",
        description="Technician started repair"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Repair started",
        "repair_id": repair.repair_id,
        "status": repair.status
    }


@router.post("/repairs/{repair_id}/parts")
def add_repair_part(
    repair_id: str,
    part_name: str = Form(...),
    old_part_serial: str | None = Form(None),
    new_part_serial: str | None = Form(None),
    warranty_months: int = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user
    )

    if repair.status not in {"IN_REPAIR", "PART_REPLACED"}:
        raise HTTPException(
            status_code=400,
            detail="Parts can only be added during repair"
        )

    if not part_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Part name cannot be empty"
        )

    if warranty_months < 0:
        raise HTTPException(
            status_code=400,
            detail="Warranty months cannot be negative"
        )

    part = RepairPart(
        repair_id=repair.id,
        part_name=part_name.strip(),
        old_part_serial=old_part_serial,
        new_part_serial=new_part_serial,
        warranty_months=warranty_months
    )

    db.add(part)
    db.commit()
    db.refresh(part)

    return {
        "message": "Repair part added",
        "part_id": part.id,
        "part_name": part.part_name
    }


@router.get("/repairs/{repair_id}/parts")
def get_repair_parts(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user
    )

    parts = (
        db.query(RepairPart)
        .filter(
            RepairPart.repair_id == repair.id
        )
        .order_by(
            RepairPart.replaced_at.asc()
        )
        .all()
    )

    return parts


@router.post("/repairs/{repair_id}/part-replaced")
def mark_part_replaced(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user
    )

    if repair.status != "IN_REPAIR":
        raise HTTPException(
            status_code=400,
            detail="Repair must be IN_REPAIR"
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
            detail="No repair parts have been added"
        )

    repair.status = "PART_REPLACED"

    history = RepairHistory(
        repair_id=repair.id,
        status="PART_REPLACED",
        description="Replacement parts recorded"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Parts marked as replaced",
        "repair_id": repair.repair_id,
        "status": repair.status
    }


@router.post("/repairs/{repair_id}/documents")
def upload_repair_document(
    repair_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user
    )

    document_type = document_type.upper()

    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid document type"
        )

    extension = Path(
        file.filename or ""
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="File type not allowed"
        )

    if repair.status not in {
        "DIAGNOSING",
        "IN_REPAIR",
        "PART_REPLACED",
        "COMPLETED"
    }:
        raise HTTPException(
            status_code=400,
            detail="Documents cannot be uploaded at this stage"
        )

    unique_name = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = DOCUMENT_FOLDER / unique_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    file_url = f"/uploads/documents/{unique_name}"

    document = RepairDocument(
        repair_id=repair.id,
        document_type=document_type,
        file_name=file.filename,
        file_url=file_url,
        description=description,
        uploaded_by=current_user.id
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "message": "Document uploaded successfully",
        "document_id": document.id,
        "document_type": document.document_type,
        "file_name": document.file_name,
        "file_url": document.file_url
    }


@router.get("/repairs/{repair_id}/documents")
def get_repair_documents(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user
    )

    documents = (
        db.query(RepairDocument)
        .filter(
            RepairDocument.repair_id == repair.id
        )
        .order_by(
            RepairDocument.created_at.desc()
        )
        .all()
    )

    return documents


@router.post("/repairs/{repair_id}/complete")
def complete_repair(
    repair_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_technician(current_user)

    repair = get_technician_repair(
        repair_id,
        db,
        current_user
    )

    if repair.status not in {
        "IN_REPAIR",
        "PART_REPLACED"
    }:
        raise HTTPException(
            status_code=400,
            detail="Repair must be in repair stage before completion"
        )

    repair.status = "COMPLETED"

    repair_hash = generate_repair_hash(
        repair_id=repair.repair_id,
        product_id=repair.product_id,
        issue_description=repair.issue_description,
        diagnosis=repair.diagnosis,
        status=repair.status
    )

    repair.record_hash = repair_hash

    history = RepairHistory(
        repair_id=repair.id,
        status="COMPLETED",
        description="Technician completed the repair"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Repair completed successfully",
        "repair_id": repair.repair_id,
        "status": repair.status,
        "record_hash": repair.record_hash
    }
