import hashlib
from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def calculate_log_hash(
    previous_hash: Optional[str],
    user_id: Optional[int],
    action: str,
    resource_type: Optional[str],
    resource_id: Optional[int],
    details: Optional[str],
    ip_address: Optional[str],
    created_at: str,
) -> str:
    """
    Generate a SHA-256 hash for an audit record.

    The previous audit record's hash is included in the
    calculation, creating a tamper-evident hash chain.
    """

    data = "|".join(
        [
            previous_hash or "",
            str(user_id) if user_id is not None else "",
            action,
            resource_type or "",
            str(resource_id)
            if resource_id is not None
            else "",
            details or "",
            ip_address or "",
            created_at,
        ]
    )

    return hashlib.sha256(
        data.encode("utf-8")
    ).hexdigest()


def create_audit_log(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """
    Create a tamper-evident audit record.

    Each new record stores the hash of the previous record.
    """

    # Get the most recent audit record
    previous_log = (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .first()
    )

    previous_hash = (
        previous_log.log_hash
        if previous_log and previous_log.log_hash
        else None
    )

    # Create the new audit record
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        previous_hash=previous_hash,
    )

    db.add(audit_log)

    # Generate the database ID and default timestamp
    db.flush()

    # Generate this record's hash
    audit_log.log_hash = calculate_log_hash(
        previous_hash=previous_hash,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        created_at=audit_log.created_at.isoformat(),
    )

    db.commit()
    db.refresh(audit_log)

    return audit_log