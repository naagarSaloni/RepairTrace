from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.repair import Repair


def calculate_trust_score(
    product: Product,
    db: Session
):
    """
    Calculate a rule-based trust score for a product.

    Score starts at 100 and decreases when the repair history
    contains signals that reduce confidence.

    This is a rule-based risk analysis system, not a claim that
    the physical repair itself is guaranteed to be genuine.
    """

    repairs = (
        db.query(Repair)
        .filter(Repair.product_id == product.id)
        .all()
    )

    score = 100
    risk_flags = []

    # ========================================================
    # 1. Number of repairs
    # ========================================================

    if len(repairs) >= 5:
        score -= 20
        risk_flags.append(
            "High number of repairs"
        )

    elif len(repairs) >= 3:
        score -= 10
        risk_flags.append(
            "Multiple repairs recorded"
        )

    # ========================================================
    # 2. Cancelled repairs
    # ========================================================

    cancelled_repairs = [
        repair
        for repair in repairs
        if repair.status == "CANCELLED"
    ]

    if cancelled_repairs:
        score -= min(
            len(cancelled_repairs) * 5,
            15
        )

        risk_flags.append(
            "Cancelled repair records detected"
        )

    # ========================================================
    # 3. Missing diagnosis
    # ========================================================

    incomplete_repairs = [
        repair
        for repair in repairs
        if not repair.diagnosis
        or not repair.diagnosis.strip()
    ]

    if incomplete_repairs:
        score -= min(
            len(incomplete_repairs) * 5,
            15
        )

        risk_flags.append(
            "Repair records missing diagnosis"
        )

    # ========================================================
    # 4. Missing cryptographic repair hash
    # ========================================================

    unhashed_repairs = [
        repair
        for repair in repairs
        if not repair.record_hash
    ]

    if unhashed_repairs:
        score -= min(
            len(unhashed_repairs) * 5,
            15
        )

        risk_flags.append(
            "Some repair records do not have a SHA-256 hash"
        )

    # ========================================================
    # 5. Repairs without blockchain transaction
    # ========================================================

    non_blockchain_repairs = [
        repair
        for repair in repairs
        if not repair.blockchain_tx_hash
    ]

    if non_blockchain_repairs:
        score -= min(
            len(non_blockchain_repairs) * 3,
            10
        )

        risk_flags.append(
            "Some repair records are not backed by a blockchain transaction"
        )

    # ========================================================
    # 6. Repair status consistency
    # ========================================================

    invalid_completed_repairs = [
        repair
        for repair in repairs
        if repair.status in {
            "COMPLETED",
            "CUSTOMER_VERIFIED",
            "RETURNED"
        }
        and not repair.diagnosis
    ]

    if invalid_completed_repairs:
        score -= min(
            len(invalid_completed_repairs) * 5,
            10
        )

        risk_flags.append(
            "Completed repairs have incomplete diagnostic information"
        )

    # ========================================================
    # Keep score within 0–100
    # ========================================================

    score = max(
        0,
        min(score, 100)
    )

    # ========================================================
    # Determine risk level
    # ========================================================

    if score >= 80:
        risk_level = "LOW"

    elif score >= 50:
        risk_level = "MEDIUM"

    else:
        risk_level = "HIGH"

    # ========================================================
    # Return analysis
    # ========================================================

    return {
        "trust_score": score,
        "risk_level": risk_level,
        "risk_flags": risk_flags,
        "total_repairs": len(repairs)
    }