from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.vendor import Vendor
from app.models.repair import Repair
from app.models.repair_history import RepairHistory
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


def require_admin(current_user: User):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )


# ============================================================
# TECHNICIANS
# ============================================================

@router.get("/technicians")
def get_technicians(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)

    technicians = (
        db.query(User)
        .filter(User.role == "TECHNICIAN")
        .all()
    )

    return [
        {
            "id": technician.id,
            "name": technician.name,
            "email": technician.email
        }
        for technician in technicians
    ]


# ============================================================
# ASSIGN TECHNICIAN
# ============================================================

@router.post("/repairs/{repair_id}/assign/{technician_id}")
def assign_technician(
    repair_id: str,
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)

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

    technician = (
        db.query(User)
        .filter(
            User.id == technician_id,
            User.role == "TECHNICIAN"
        )
        .first()
    )

    if not technician:
        raise HTTPException(
            status_code=404,
            detail="Technician not found"
        )

    repair.technician_id = technician.id
    repair.status = "RECEIVED"

    history = RepairHistory(
        repair_id=repair.id,
        status="RECEIVED",
        description=f"Technician {technician.name} assigned"
    )

    db.add(history)
    db.commit()
    db.refresh(repair)

    return {
        "message": "Technician assigned successfully",
        "repair_id": repair.repair_id,
        "technician_id": technician.id,
        "status": repair.status
    }


# ============================================================
# CREATE VENDOR PROFILE
# ============================================================

@router.post("/vendors")
def create_vendor(
    user_id: int,
    business_name: str,
    phone: str | None = None,
    address: str | None = None,
    specialization: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.role != "TECHNICIAN":
        raise HTTPException(
            status_code=400,
            detail="Only a technician can be registered as a repair vendor"
        )

    existing_vendor = (
        db.query(Vendor)
        .filter(Vendor.user_id == user_id)
        .first()
    )

    if existing_vendor:
        raise HTTPException(
            status_code=400,
            detail="Vendor profile already exists for this user"
        )

    vendor = Vendor(
        user_id=user_id,
        business_name=business_name,
        phone=phone,
        address=address,
        specialization=specialization,
        verification_status="PENDING"
    )

    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    return {
        "message": "Vendor profile created successfully",
        "vendor": {
            "id": vendor.id,
            "user_id": vendor.user_id,
            "business_name": vendor.business_name,
            "phone": vendor.phone,
            "address": vendor.address,
            "specialization": vendor.specialization,
            "verification_status": vendor.verification_status
        }
    }


# ============================================================
# GET ALL VENDORS
# ============================================================

@router.get("/vendors")
def get_vendors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)

    vendors = db.query(Vendor).all()

    result = []

    for vendor in vendors:
        user = (
            db.query(User)
            .filter(User.id == vendor.user_id)
            .first()
        )

        result.append({
            "id": vendor.id,
            "user_id": vendor.user_id,
            "name": user.name if user else None,
            "email": user.email if user else None,
            "business_name": vendor.business_name,
            "phone": vendor.phone,
            "address": vendor.address,
            "specialization": vendor.specialization,
            "verification_status": vendor.verification_status,
            "verified_at": vendor.verified_at,
            "created_at": vendor.created_at
        })

    return result


# ============================================================
# GET SINGLE VENDOR
# ============================================================

@router.get("/vendors/{vendor_id}")
def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)

    vendor = (
        db.query(Vendor)
        .filter(Vendor.id == vendor_id)
        .first()
    )

    if not vendor:
        raise HTTPException(
            status_code=404,
            detail="Vendor not found"
        )

    user = (
        db.query(User)
        .filter(User.id == vendor.user_id)
        .first()
    )

    return {
        "id": vendor.id,
        "user_id": vendor.user_id,
        "name": user.name if user else None,
        "email": user.email if user else None,
        "business_name": vendor.business_name,
        "phone": vendor.phone,
        "address": vendor.address,
        "specialization": vendor.specialization,
        "verification_status": vendor.verification_status,
        "verified_at": vendor.verified_at,
        "created_at": vendor.created_at
    }


# ============================================================
# VERIFY VENDOR
# ============================================================

@router.patch("/vendors/{vendor_id}/verify")
def verify_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)

    vendor = (
        db.query(Vendor)
        .filter(Vendor.id == vendor_id)
        .first()
    )

    if not vendor:
        raise HTTPException(
            status_code=404,
            detail="Vendor not found"
        )

    vendor.verification_status = "VERIFIED"
    vendor.verified_at = datetime.utcnow()

    db.commit()
    db.refresh(vendor)

    return {
        "message": "Vendor verified successfully",
        "vendor_id": vendor.id,
        "verification_status": vendor.verification_status,
        "verified_at": vendor.verified_at
    }


# ============================================================
# REJECT VENDOR
# ============================================================

@router.patch("/vendors/{vendor_id}/reject")
def reject_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_admin(current_user)

    vendor = (
        db.query(Vendor)
        .filter(Vendor.id == vendor_id)
        .first()
    )

    if not vendor:
        raise HTTPException(
            status_code=404,
            detail="Vendor not found"
        )

    vendor.verification_status = "REJECTED"
    vendor.verified_at = None

    db.commit()
    db.refresh(vendor)

    return {
        "message": "Vendor rejected successfully",
        "vendor_id": vendor.id,
        "verification_status": vendor.verification_status
    }