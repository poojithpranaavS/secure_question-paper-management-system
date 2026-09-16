from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.question_paper import QuestionPaper
from app.models.user import User
from app.security.authorization import require_roles
from app.services.audit import create_audit_log


router = APIRouter(
    prefix="/release",
    tags=["Controlled Release"],
)


# ---------------------------------------------------------
# Request model
# ---------------------------------------------------------


class ScheduleReleaseRequest(BaseModel):
    release_at: datetime


# ---------------------------------------------------------
# Schedule question-paper release
# ---------------------------------------------------------


@router.post("/{question_paper_id}/schedule")
def schedule_release(
    question_paper_id: int,
    request: ScheduleReleaseRequest,
    current_user: User = Depends(
        require_roles("EXAM_AUTHORITY")
    ),
    db: Session = Depends(get_db),
):
    """
    Schedule an approved question paper for controlled release.

    Only EXAM_AUTHORITY users can schedule releases.
    A question paper must already be APPROVED.
    The release time must be in the future.
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

    if question_paper.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Only approved question papers can be "
                "scheduled for release."
            ),
        )

    release_at = request.release_at

    # Treat timezone-naive input as UTC.
    if release_at.tzinfo is None:
        release_at = release_at.replace(
            tzinfo=timezone.utc
        )

    release_at = release_at.astimezone(
        timezone.utc
    )

    now = datetime.now(timezone.utc)

    if release_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Release time must be in the future.",
        )

    question_paper.scheduled_release_at = (
        release_at.replace(tzinfo=None)
    )

    question_paper.released_at = None

    db.commit()
    db.refresh(question_paper)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="QUESTION_PAPER_RELEASE_SCHEDULED",
        resource_type="QuestionPaper",
        resource_id=question_paper.id,
        details=(
            f"Question paper '{question_paper.title}' "
            f"scheduled for release at "
            f"{release_at.isoformat()}."
        ),
        ip_address=None,
    )

    return {
        "message": "Question paper release scheduled successfully.",
        "question_paper": {
            "id": question_paper.id,
            "title": question_paper.title,
            "status": question_paper.status,
            "scheduled_release_at": (
                question_paper.scheduled_release_at
            ),
            "released_at": question_paper.released_at,
        },
        "security": {
            "release_role": "EXAM_AUTHORITY",
            "approved_before_release": True,
            "audit_logged": True,
        },
    }


# ---------------------------------------------------------
# Release status
# ---------------------------------------------------------


@router.get("/{question_paper_id}/status")
def get_release_status(
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
    Return the controlled-release status of a question paper.

    When the scheduled release time has passed, the system
    marks the paper as RELEASED.
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

    now = datetime.utcnow()

    if (
        question_paper.status == "APPROVED"
        and question_paper.scheduled_release_at is not None
        and question_paper.released_at is None
        and question_paper.scheduled_release_at <= now
    ):
        question_paper.status = "RELEASED"
        question_paper.released_at = now

        db.commit()
        db.refresh(question_paper)

        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="QUESTION_PAPER_RELEASED",
            resource_type="QuestionPaper",
            resource_id=question_paper.id,
            details=(
                f"Question paper '{question_paper.title}' "
                f"became available after reaching its "
                f"scheduled release time."
            ),
            ip_address=None,
        )

    if question_paper.status == "RELEASED":
        release_state = "RELEASED"

    elif question_paper.scheduled_release_at is not None:
        release_state = "SCHEDULED"

    else:
        release_state = "NOT_SCHEDULED"

    return {
        "question_paper": {
            "id": question_paper.id,
            "title": question_paper.title,
            "status": question_paper.status,
            "release_state": release_state,
            "scheduled_release_at": (
                question_paper.scheduled_release_at
            ),
            "released_at": question_paper.released_at,
        }
    }