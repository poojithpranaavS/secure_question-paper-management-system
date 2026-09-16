import hashlib

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.security.authorization import require_roles


router = APIRouter(
    prefix="/audit",
    tags=["Audit & Transparency"],
)


def calculate_expected_hash(log: AuditLog) -> str:
    data = "|".join(
        [
            log.previous_hash or "",
            str(log.user_id) if log.user_id is not None else "",
            log.action,
            log.resource_type or "",
            str(log.resource_id)
            if log.resource_id is not None
            else "",
            log.details or "",
            log.ip_address or "",
            log.created_at.isoformat(),
        ]
    )

    return hashlib.sha256(
        data.encode("utf-8")
    ).hexdigest()


@router.get("/logs")
def get_audit_logs(
    current_user: User = Depends(
        require_roles(
            "AUDITOR",
            "EXAM_AUTHORITY",
            "ADMIN",
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Return the security audit trail.
    """

    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .all()
    )

    return {
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at,
                "previous_hash": log.previous_hash,
                "log_hash": log.log_hash,
            }
            for log in logs
        ],
    }


@router.get("/verify")
def verify_audit_chain(
    current_user: User = Depends(
        require_roles(
            "AUDITOR",
            "EXAM_AUTHORITY",
            "ADMIN",
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Verify the integrity of the complete audit hash chain.
    """

    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.id.asc())
        .all()
    )

    if not logs:
        return {
            "valid": True,
            "message": "Audit chain is empty.",
            "checked_logs": 0,
        }

    previous_hash = None

    for log in logs:

        # Verify that this record points to the correct
        # previous audit record.
        if log.previous_hash != previous_hash:
            return {
                "valid": False,
                "message": "Audit chain integrity violation detected.",
                "failed_log_id": log.id,
                "reason": "Previous hash mismatch.",
            }

        # Recalculate this record's hash.
        expected_hash = calculate_expected_hash(log)

        if log.log_hash != expected_hash:
            return {
                "valid": False,
                "message": "Audit chain integrity violation detected.",
                "failed_log_id": log.id,
                "reason": "Log hash mismatch.",
            }

        previous_hash = log.log_hash

    return {
        "valid": True,
        "message": "Audit chain integrity verified successfully.",
        "checked_logs": len(logs),
    }