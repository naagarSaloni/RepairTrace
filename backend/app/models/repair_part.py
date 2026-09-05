from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RepairPart(Base):
    __tablename__ = "repair_parts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    repair_id: Mapped[int] = mapped_column(
        ForeignKey("repairs.id"),
        nullable=False
    )

    part_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    old_part_serial: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    new_part_serial: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    warranty_months: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    blockchain_tx_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    replaced_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )