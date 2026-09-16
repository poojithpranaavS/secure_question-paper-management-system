from sqlalchemy import inspect, text

from app.database.connection import engine


def migrate_audit_table():
    inspector = inspect(engine)

    columns = {
        column["name"]
        for column in inspector.get_columns("audit_logs")
    }

    with engine.begin() as connection:

        if "previous_hash" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE audit_logs "
                    "ADD COLUMN previous_hash VARCHAR(64)"
                )
            )
            print("Added previous_hash column.")

        if "log_hash" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE audit_logs "
                    "ADD COLUMN log_hash VARCHAR(64)"
                )
            )
            print("Added log_hash column.")

    print("Audit table migration completed.")


if __name__ == "__main__":
    migrate_audit_table()