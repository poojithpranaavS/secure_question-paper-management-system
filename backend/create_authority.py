import os

from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.models.user import User
from app.security.authentication import hash_password


load_dotenv()


AUTHORITY_EMAIL = os.getenv(
    "AUTHORITY_EMAIL",
    "authority@exam.gov",
)

AUTHORITY_PASSWORD = os.getenv(
    "AUTHORITY_PASSWORD",
)


def create_authority():
    print("Starting authority account setup...")

    if not AUTHORITY_PASSWORD:
        print(
            "ERROR: AUTHORITY_PASSWORD is not configured "
            "in the environment."
        )
        return

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(
                User.email == AUTHORITY_EMAIL
            )
            .first()
        )

        if existing_user:
            print(
                "EXAM_AUTHORITY account already exists."
            )
            print(
                f"Email: {AUTHORITY_EMAIL}"
            )
            print(
                f"Role: {existing_user.role}"
            )
            return

        authority = User(
            full_name="Exam Authority",
            email=AUTHORITY_EMAIL,
            password_hash=hash_password(
                AUTHORITY_PASSWORD
            ),
            role="EXAM_AUTHORITY",
            is_active=True,
            mfa_enabled=False,
        )

        db.add(authority)
        db.commit()
        db.refresh(authority)

        print()
        print("============================================")
        print("EXAM_AUTHORITY ACCOUNT CREATED")
        print("============================================")
        print(f"ID       : {authority.id}")
        print(f"Name     : {authority.full_name}")
        print(f"Email    : {authority.email}")
        print(f"Role     : {authority.role}")
        print("Password : Loaded from environment")
        print("============================================")

    except Exception as e:
        db.rollback()
        print("ERROR:", e)

    finally:
        db.close()


if __name__ == "__main__":
    create_authority()