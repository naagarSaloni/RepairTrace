from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Repair(Base):
    __tablename__ = "repairs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    repair_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    technician_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    issue_description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    diagnosis: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "SUBMITTED",
            "RECEIVED",
            "DIAGNOSING",
            "AWAITING_APPROVAL",
            "APPROVED",
            "IN_REPAIR",
            "PART_REPLACED",
            "COMPLETED",
            "RETURNED",
            "CANCELLED",
            name="repair_status"
        ),
        default="SUBMITTED",
        nullable=False
    )

    blockchain_tx_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )