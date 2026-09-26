from app.db.database import SessionLocal
from app.models.repair import Repair
from app.services.blockchain import generate_repair_hash


db = SessionLocal()

repair = (
    db.query(Repair)
    .filter(
        Repair.repair_id == "REP-5A92132D21"
    )
    .first()
)

if not repair:
    print("Repair not found")
else:
    repair.record_hash = generate_repair_hash(
        repair_id=repair.repair_id,
        product_id=repair.product_id,
        issue_description=repair.issue_description,
        diagnosis=repair.diagnosis
    )

    db.commit()

    print("Hash updated successfully")
    print("Repair ID:", repair.repair_id)
    print("New hash:", repair.record_hash)

db.close()