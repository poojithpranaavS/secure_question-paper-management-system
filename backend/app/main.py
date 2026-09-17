import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import Base, engine, SessionLocal
from app.models import AuditLog, QuestionPaper, User

from app.routes.approvals import router as approval_router
from app.routes.audit import router as audit_router
from app.routes.auth import router as auth_router
from app.routes.downloads import router as download_router
from app.routes.question_papers import (
    router as question_paper_router,
)
from app.routes.release import router as release_router

from app.security.authentication import hash_password
from app.security.authorization import (
    get_current_user,
    require_roles,
)


# ---------------------------------------------------------
# Database initialization
# ---------------------------------------------------------

# Create all registered database tables
Base.metadata.create_all(bind=engine)


def initialize_authority_account():
    """
    Create the Exam Authority account if it does not already exist.

    This makes the cloud deployment self-initializing while keeping
    the operation idempotent. Existing users are not modified.
    """
    authority_email = os.getenv("AUTHORITY_EMAIL")
    authority_password = os.getenv("AUTHORITY_PASSWORD")

    if not authority_email or not authority_password:
        print(
            "AUTHORITY_EMAIL or AUTHORITY_PASSWORD is not configured. "
            "Authority account initialization skipped."
        )
        return

    db = SessionLocal()

    try:
        existing_user = (
            db.query(User)
            .filter(User.email == authority_email)
            .first()
        )

        if existing_user:
            print(
                f"Authority account already exists: {authority_email}"
            )
            return

        authority = User(
            full_name="Exam Authority",
            email=authority_email,
            password_hash=hash_password(authority_password),
            role="EXAM_AUTHORITY",
            is_active=True,
        )

        db.add(authority)
        db.commit()

        print(
            f"Exam Authority account created: {authority_email}"
        )

    except Exception as exc:
        db.rollback()
        print(
            f"Authority account initialization failed: {exc}"
        )

    finally:
        db.close()


# Initialize required system account
initialize_authority_account()


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Secure Question Paper Management System",
    description=(
        "A secure cloud-based platform for managing, "
        "auditing, and controlling examination question papers."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://secure-question-paper-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Application routers
# ---------------------------------------------------------

app.include_router(auth_router)
app.include_router(question_paper_router)
app.include_router(approval_router)
app.include_router(audit_router)
app.include_router(release_router)
app.include_router(download_router)


# ---------------------------------------------------------
# Basic endpoints
# ---------------------------------------------------------


@app.get("/")
def root():
    return {
        "system": "Secure Question Paper Management System",
        "status": "operational",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "backend",
    }


# ---------------------------------------------------------
# Authentication test endpoint
# ---------------------------------------------------------


@app.get("/protected")
def protected_endpoint(
    current_user: User = Depends(
        get_current_user
    ),
):
    return {
        "message": "Authenticated access granted.",
        "user": current_user.full_name,
        "role": current_user.role,
    }


# ---------------------------------------------------------
# RBAC test endpoint
# ---------------------------------------------------------


@app.get("/authority-only")
def authority_only(
    current_user: User = Depends(
        require_roles("EXAM_AUTHORITY")
    ),
):
    return {
        "message": "Exam Authority access granted.",
        "user": current_user.full_name,
        "role": current_user.role,
    }