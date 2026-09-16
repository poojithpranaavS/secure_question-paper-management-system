from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database.connection import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    action = Column(
        String(100),
        nullable=False,
        index=True,
    )

    resource_type = Column(
        String(100),
        nullable=True,
    )

    resource_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    details = Column(
        Text,
        nullable=True,
    )

    ip_address = Column(
        String(45),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------
    # Tamper-evident hash chain
    # -----------------------------------------------------

    previous_hash = Column(
        String(64),
        nullable=True,
    )

    log_hash = Column(
        String(64),
        nullable=True,
        index=True,
    )