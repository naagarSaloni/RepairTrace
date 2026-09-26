import hashlib
import json


def generate_repair_hash(
    repair_id: str,
    product_id: int,
    issue_description: str,
    diagnosis: str | None
) -> str:

    repair_data = {
        "repair_id": repair_id,
        "product_id": product_id,
        "issue_description": issue_description,
        "diagnosis": diagnosis
    }

    serialized_data = json.dumps(
        repair_data,
        sort_keys=True,
        default=str
    )

    return hashlib.sha256(
        serialized_data.encode("utf-8")
    ).hexdigest()


def verify_repair_hash(
    repair_id: str,
    product_id: int,
    issue_description: str,
    diagnosis: str | None,
    stored_hash: str
) -> bool:

    current_hash = generate_repair_hash(
        repair_id=repair_id,
        product_id=product_id,
        issue_description=issue_description,
        diagnosis=diagnosis
    )

    return current_hash == stored_hash