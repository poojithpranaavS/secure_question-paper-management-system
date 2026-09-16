from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.question_paper import QuestionPaper
from app.models.user import User
from app.security.authorization import require_roles
from app.services.audit import create_audit_log


router = APIRouter(
    prefix="/approvals",
    tags=["Question Paper Approvals"],
)


# ---------------------------------------------------------
# Request models
# ---------------------------------------------------------


class RejectionRequest(BaseModel):
    reason: str = Field(
        min_length=5,
        max_length=1000,
    )


# ---------------------------------------------------------
# Approve question paper
# ---------------------------------------------------------


@router.post("/{question_paper_id}/approve")
def approve_question_paper(
    question_paper_id: int,
    current_user: User = Depends(
        require_roles("EXAM_AUTHORITY")
    ),
    db: Session = Depends(get_db),
):
    """
    Approve a question paper.

    Security controls:
    - EXAM_AUTHORITY role required
    - Self-approval prohibited
    - Only PENDING_APPROVAL papers can be approved
    - Approval is recorded
    - Audit event is created
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

    if question_paper.created_by == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Self-approval is prohibited. "
                "The uploader cannot approve their own "
                "question paper."
            ),
        )

    if question_paper.status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Question paper cannot be approved because "
                f"its current status is "
                f"'{question_paper.status}'."
            ),
        )

    question_paper.status = "APPROVED"
    question_paper.approved_by = current_user.id
    question_paper.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(question_paper)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUESTION_PAPER_APPROVED",
        resource_type="QuestionPaper",
        resource_id=question_paper.id,
        details=(
            f"Question paper '{question_paper.title}' "
            f"approved by Exam Authority."
        ),
        ip_address=None,
    )

    return {
        "message": "Question paper approved successfully.",
        "question_paper": {
            "id": question_paper.id,
            "title": question_paper.title,
            "examination_name": question_paper.examination_name,
            "subject": question_paper.subject,
            "status": question_paper.status,
            "created_by": question_paper.created_by,
            "approved_by": question_paper.approved_by,
            "approved_at": question_paper.approved_at,
        },
        "security": {
            "approval_role": "EXAM_AUTHORITY",
            "separation_of_duties": True,
            "audit_logged": True,
        },
    }


# ---------------------------------------------------------
# Reject question paper
# ---------------------------------------------------------


@router.post("/{question_paper_id}/reject")
def reject_question_paper(
    question_paper_id: int,
    request: RejectionRequest,
    current_user: User = Depends(
        require_roles("EXAM_AUTHORITY")
    ),
    db: Session = Depends(get_db),
):
    """
    Reject a question paper.

    Security controls:
    - EXAM_AUTHORITY role required
    - Self-rejection prohibited
    - Only PENDING_APPROVAL papers can be rejected
    - Rejection reason is recorded
    - Rejecting authority is recorded
    - Audit event is created
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

    if question_paper.created_by == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Self-rejection is prohibited. "
                "The uploader cannot reject their own "
                "question paper."
            ),
        )

    if question_paper.status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Question paper cannot be rejected because "
                f"its current status is "
                f"'{question_paper.status}'."
            ),
        )

    reason = request.reason.strip()

    if not reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A rejection reason is required.",
        )

    question_paper.status = "REJECTED"
    question_paper.rejected_by = current_user.id
    question_paper.rejected_at = datetime.utcnow()
    question_paper.rejection_reason = reason

    db.commit()
    db.refresh(question_paper)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUESTION_PAPER_REJECTED",
        resource_type="QuestionPaper",
        resource_id=question_paper.id,
        details=(
            f"Question paper '{question_paper.title}' "
            f"rejected by Exam Authority. "
            f"Reason: {reason}"
        ),
        ip_address=None,
    )

    return {
        "message": "Question paper rejected successfully.",
        "question_paper": {
            "id": question_paper.id,
            "title": question_paper.title,
            "examination_name": question_paper.examination_name,
            "subject": question_paper.subject,
            "status": question_paper.status,
            "created_by": question_paper.created_by,
            "rejected_by": question_paper.rejected_by,
            "rejected_at": question_paper.rejected_at,
            "rejection_reason": question_paper.rejection_reason,
        },
        "security": {
            "rejection_role": "EXAM_AUTHORITY",
            "separation_of_duties": True,
            "reason_recorded": True,
            "audit_logged": True,
        },
    }


# ---------------------------------------------------------
# Pending question papers
# ---------------------------------------------------------


@router.get("/pending")
def get_pending_question_papers(
    current_user: User = Depends(
        require_roles("EXAM_AUTHORITY")
    ),
    db: Session = Depends(get_db),
):
    """
    Return all question papers waiting for approval.
    """

    papers = (
        db.query(QuestionPaper)
        .filter(
            QuestionPaper.status == "PENDING_APPROVAL"
        )
        .order_by(
            QuestionPaper.created_at.asc()
        )
        .all()
    )

    return {
        "count": len(papers),
        "papers": [
            {
                "id": paper.id,
                "title": paper.title,
                "examination_name": paper.examination_name,
                "subject": paper.subject,
                "file_name": paper.file_name,
                "status": paper.status,
                "created_by": paper.created_by,
                "created_at": paper.created_at,
            }
            for paper in papers
        ],
    }