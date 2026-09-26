from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RepairDocument(Base):
    __tablename__ = "repair_documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    repair_id: Mapped[int] = mapped_column(
        ForeignKey("repairs.id"),
        nullable=False,
        index=True
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    file_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )