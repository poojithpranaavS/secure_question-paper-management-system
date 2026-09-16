from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

import hashlib

from app.database.connection import get_db
from app.models.question_paper import QuestionPaper
from app.models.user import User
from app.security.authorization import require_roles
from app.security.encryption import decrypt_file
from app.services.audit import create_audit_log


router = APIRouter(
    prefix="/downloads",
    tags=["Secure Downloads"],
)


STORAGE_DIRECTORY = Path(
    "secure_storage/question_papers"
).resolve()


def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@router.get("/{question_paper_id}")
def download_question_paper(
    question_paper_id: int,
    current_user: User = Depends(
        require_roles(
            "EXAM_AUTHORITY",
            "AUDITOR",
            "ADMIN",
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Securely download a released question paper.

    Security controls:
    - Role-based authorization
    - Release-status enforcement
    - Encrypted file storage
    - AES-256-GCM decryption
    - SHA-256 integrity verification
    - Path validation
    - Download audit logging
    """

    question_paper = (
        db.query(QuestionPaper)
        .filter(
            QuestionPaper.id == question_paper_id
        )
        .first()
    )

    if question_paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question paper not found.",
        )

    # -----------------------------------------------------
    # Release enforcement
    # -----------------------------------------------------

    if question_paper.status != "RELEASED":

        if (
            question_paper.status == "APPROVED"
            and question_paper.scheduled_release_at
            and question_paper.scheduled_release_at
            <= datetime.utcnow()
        ):
            question_paper.status = "RELEASED"
            question_paper.released_at = datetime.utcnow()

            db.commit()
            db.refresh(question_paper)

            create_audit_log(
                db=db,
                user_id=current_user.id,
                action="QUESTION_PAPER_RELEASED",
                resource_type="QuestionPaper",
                resource_id=question_paper.id,
                details=(
                    f"Question paper "
                    f"'{question_paper.title}' "
                    f"became released after reaching "
                    f"its scheduled release time."
                ),
                ip_address=None,
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Question paper is not available for "
                    "download. It has not been released."
                ),
            )

    # -----------------------------------------------------
    # Validate stored path
    # -----------------------------------------------------

    stored_path = Path(
        question_paper.file_path
    ).resolve()

    try:
        stored_path.relative_to(
            STORAGE_DIRECTORY
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid secure storage path.",
        )

    if not stored_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encrypted question paper file not found.",
        )

    if not stored_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored question paper is invalid.",
        )

    # -----------------------------------------------------
    # Read encrypted file
    # -----------------------------------------------------

    try:
        encrypted_data = stored_path.read_bytes()

    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to read encrypted question paper.",
        ) from exc

    # -----------------------------------------------------
    # Decrypt
    # -----------------------------------------------------

    try:
        decrypted_data = decrypt_file(
            encrypted_data
        )

    except Exception as exc:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="QUESTION_PAPER_DECRYPTION_FAILED",
            resource_type="QuestionPaper",
            resource_id=question_paper.id,
            details=(
                f"Decryption failed for question paper "
                f"'{question_paper.title}'."
            ),
            ip_address=None,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to decrypt the question paper."
            ),
        ) from exc

    # -----------------------------------------------------
    # Integrity verification
    # -----------------------------------------------------

    calculated_hash = calculate_sha256(
        decrypted_data
    )

    if calculated_hash != question_paper.file_hash:

        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="QUESTION_PAPER_INTEGRITY_FAILURE",
            resource_type="QuestionPaper",
            resource_id=question_paper.id,
            details=(
                f"SHA-256 integrity verification failed "
                f"for question paper "
                f"'{question_paper.title}'."
            ),
            ip_address=None,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Question paper integrity verification failed."
            ),
        )

    # -----------------------------------------------------
    # Audit successful download
    # -----------------------------------------------------

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUESTION_PAPER_DOWNLOADED",
        resource_type="QuestionPaper",
        resource_id=question_paper.id,
        details=(
            f"Question paper '{question_paper.title}' "
            f"securely decrypted and downloaded."
        ),
        ip_address=None,
    )

    # -----------------------------------------------------
    # Return decrypted PDF
    # -----------------------------------------------------

    safe_filename = Path(
        question_paper.file_name
    ).name

    response = StreamingResponse(
        BytesIO(decrypted_data),
        media_type="application/pdf",
    )

    response.headers[
        "Content-Disposition"
    ] = (
        f'attachment; filename="{safe_filename}"'
    )

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "Cache-Control"
    ] = "no-store"

    return response