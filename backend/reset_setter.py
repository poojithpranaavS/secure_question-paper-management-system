from app.database.connection import SessionLocal
from app.models.user import User
from app.security.authentication import hash_password


SETTER_EMAIL = "setter@test.com"
NEW_PASSWORD = "Setter@12345"


def reset_setter_password():
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == SETTER_EMAIL)
            .first()
        )

        if user is None:
            print("Question Setter account not found.")
            return

        user.password_hash = hash_password(NEW_PASSWORD)
        user.role = "QUESTION_SETTER"
        user.is_active = True

        db.commit()

        print()
        print("============================================")
        print("QUESTION_SETTER PASSWORD RESET")
        print("============================================")
        print(f"Email    : {SETTER_EMAIL}")
        print(f"Password : {NEW_PASSWORD}")
        print(f"Role     : {user.role}")
        print("============================================")

    except Exception as e:
        db.rollback()
        print("ERROR:", e)

    finally:
        db.close()


if __name__ == "__main__":
    reset_setter_password()