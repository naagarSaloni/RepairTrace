from pydantic import BaseModel


class RepairCreate(BaseModel):
    product_id: int
    issue_description: str


class RepairResponse(BaseModel):
    id: int
    repair_id: str
    product_id: int
    customer_id: int
    technician_id: int | None
    issue_description: str
    diagnosis: str | None
    status: str
    blockchain_tx_hash: str | None

    class Config:
        from_attributes = True