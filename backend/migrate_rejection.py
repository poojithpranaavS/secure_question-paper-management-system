from sqlalchemy import inspect, text

from app.database.connection import engine


def migrate_rejection():
    inspector = inspect(engine)

    columns = {
        column["name"]
        for column in inspector.get_columns(
            "question_papers"
        )
    }

    with engine.begin() as connection:

        if "rejected_by" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE question_papers "
                    "ADD COLUMN rejected_by INTEGER"
                )
            )
            print("Added rejected_by column.")
        else:
            print("rejected_by column already exists.")

        if "rejected_at" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE question_papers "
                    "ADD COLUMN rejected_at DATETIME"
                )
            )
            print("Added rejected_at column.")
        else:
            print("rejected_at column already exists.")

        if "rejection_reason" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE question_papers "
                    "ADD COLUMN rejection_reason TEXT"
                )
            )
            print("Added rejection_reason column.")
        else:
            print(
                "rejection_reason column already exists."
            )

    print("Rejection workflow migration completed.")


if __name__ == "__main__":
    migrate_rejection()