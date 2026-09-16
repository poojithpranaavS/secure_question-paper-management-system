from app.database.connection import SessionLocal
from app.models.audit_log import AuditLog
from app.services.audit import calculate_log_hash


def backfill_audit_hashes():
    db = SessionLocal()

    try:
        logs = (
            db.query(AuditLog)
            .order_by(AuditLog.id.asc())
            .all()
        )

        if not logs:
            print("No audit logs found.")
            return

        previous_hash = None

        for log in logs:
            log.previous_hash = previous_hash

            log.log_hash = calculate_log_hash(
                previous_hash=previous_hash,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at.isoformat(),
            )

            previous_hash = log.log_hash

            print(
                f"Audit log {log.id} hashed successfully."
            )

        db.commit()

        print()
        print("============================================")
        print("AUDIT HASH CHAIN CREATED")
        print("============================================")
        print(f"Logs processed: {len(logs)}")
        print("Audit chain is ready for verification.")
        print("============================================")

    except Exception as e:
        db.rollback()
        print("ERROR:", e)

    finally:
        db.close()


if __name__ == "__main__":
    backfill_audit_hashes()