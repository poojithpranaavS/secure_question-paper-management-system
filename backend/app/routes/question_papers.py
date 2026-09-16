import hashlib
import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.question_paper import QuestionPaper
from app.models.user import User
from app.security.authorization import require_roles
from app.security.encryption import encrypt_file
from app.services.audit import create_audit_log


router = APIRouter(
    prefix="/question-papers",
    tags=["Question Papers"],
)


STORAGE_DIRECTORY = Path("secure_storage/question_papers")

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_CONTENT_TYPE = "application/pdf"


def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_question_paper(
    title: str = Form(...),
    examination_name: str = Form(...),
    subject: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(
        require_roles("QUESTION_SETTER")
    ),
    db: Session = Depends(get_db),
):
    """
    Secure question-paper upload.

    Security controls:
    - JWT authentication
    - RBAC authorization
    - PDF validation
    - 10 MB file-size restriction
    - PDF signature verification
    - SHA-256 integrity hash
    - AES-256-GCM encryption
    - Random storage filename
    - Audit logging
    - Approval workflow
    """

    # ---------------------------------------------------------
    # 1. Validate file type
    # ---------------------------------------------------------

    if file.content_type != ALLOWED_CONTENT_TYPE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF question papers are allowed.",
        )

    # ---------------------------------------------------------
    # 2. Validate filename
    # ---------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid file name is required.",
        )

    original_filename = Path(file.filename).name

    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must have a .pdf extension.",
        )

    # ---------------------------------------------------------
    # 3. Read uploaded file
    # ---------------------------------------------------------

    file_content = await file.read()

    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Question paper exceeds the 10 MB size limit.",
        )

    # ---------------------------------------------------------
    # 4. Verify actual PDF signature
    # ---------------------------------------------------------

    if not file_content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid PDF.",
        )

    # ---------------------------------------------------------
    # 5. Calculate SHA-256
    # ---------------------------------------------------------

    file_hash = calculate_sha256(file_content)

    # ---------------------------------------------------------
    # 6. Encrypt PDF
    # ---------------------------------------------------------

    try:
        encrypted_content = encrypt_file(file_content)

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    # ---------------------------------------------------------
    # 7. Create secure storage directory
    # ---------------------------------------------------------

    STORAGE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # 8. Generate unpredictable storage filename
    # ---------------------------------------------------------

    random_name = os.urandom(16).hex()

    stored_filename = f"{random_name}.enc"

    stored_path = STORAGE_DIRECTORY / stored_filename

    # ---------------------------------------------------------
    # 9. Store encrypted file
    # ---------------------------------------------------------

    stored_path.write_bytes(encrypted_content)

    # ---------------------------------------------------------
    # 10. Create question-paper database record
    # ---------------------------------------------------------

    question_paper = QuestionPaper(
        title=title.strip(),
        examination_name=examination_name.strip(),
        subject=subject.strip(),
        description=description.strip() if description else None,
        file_name=original_filename,
        file_path=str(stored_path),
        file_hash=file_hash,
        status="PENDING_APPROVAL",
        created_by=current_user.id,
    )

    db.add(question_paper)
    db.commit()
    db.refresh(question_paper)

    # ---------------------------------------------------------
    # 11. Create audit record
    # ---------------------------------------------------------

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUESTION_PAPER_UPLOADED",
        resource_type="QuestionPaper",
        resource_id=question_paper.id,
        details=(
            f"Question paper '{question_paper.title}' uploaded "
            f"successfully and encrypted."
        ),
        ip_address=None,
    )

    # ---------------------------------------------------------
    # 12. Return safe metadata
    # ---------------------------------------------------------

    return {
        "message": "Question paper uploaded and encrypted successfully.",
        "question_paper": {
            "id": question_paper.id,
            "title": question_paper.title,
            "examination_name": question_paper.examination_name,
            "subject": question_paper.subject,
            "file_name": question_paper.file_name,
            "sha256": question_paper.file_hash,
            "status": question_paper.status,
            "created_by": question_paper.created_by,
            "created_at": question_paper.created_at,
        },
        "security": {
            "encryption": "AES-256-GCM",
            "integrity": "SHA-256",
            "storage": "Encrypted",
            "audit_logged": True,
        },
    }