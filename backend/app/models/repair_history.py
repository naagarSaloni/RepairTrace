from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RepairHistory(Base):
    __tablename__ = "repair_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    repair_id: Mapped[int] = mapped_column(
        ForeignKey("repairs.id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    blockchain_tx_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )