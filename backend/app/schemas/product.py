from pydantic import BaseModel


class ProductCreate(BaseModel):
    product_name: str
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None


class ProductResponse(BaseModel):
    id: int
    product_uid: str
    owner_id: int
    product_name: str
    brand: str | None
    model: str | None
    serial_number: str | None
    qr_code: str | None

    class Config:
        from_attributes = True