from sqlalchemy import inspect, text

from app.database.connection import engine


def migrate_mfa():
    inspector = inspect(engine)

    columns = {
        column["name"]
        for column in inspector.get_columns("users")
    }

    with engine.begin() as connection:

        if "mfa_enabled" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN mfa_enabled "
                    "BOOLEAN NOT NULL DEFAULT 0"
                )
            )

            print("Added mfa_enabled column.")
        else:
            print("mfa_enabled column already exists.")

        if "mfa_secret" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN mfa_secret VARCHAR(512)"
                )
            )

            print("Added mfa_secret column.")
        else:
            print("mfa_secret column already exists.")

    print("MFA database migration completed.")


if __name__ == "__main__":
    migrate_mfa()