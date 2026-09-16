from datetime import datetime, timedelta, timezone
import os

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.security.authentication import (
    hash_password,
    verify_password,
)
from app.security.authorization import get_current_user
from app.security.mfa import (
    create_provisioning_uri,
    decrypt_mfa_secret,
    encrypt_mfa_secret,
    generate_mfa_secret,
    verify_totp_code,
)
from app.services.audit import create_audit_log


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "development-secret-change-before-production",
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30

MFA_CHALLENGE_EXPIRE_MINUTES = 5


# ---------------------------------------------------------
# Request models
# ---------------------------------------------------------


class RegisterRequest(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: str = Field(
        min_length=5,
        max_length=255,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class LoginRequest(BaseModel):
    email: str
    password: str


class MFACodeRequest(BaseModel):
    code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


class MFADisableRequest(BaseModel):
    password: str = Field(
        min_length=8,
        max_length=128,
    )

    code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


# ---------------------------------------------------------
# JWT creation
# ---------------------------------------------------------


def create_access_token(
    user: User,
    mfa_verified: bool = True,
) -> str:
    """
    Create the final authenticated access token.
    """

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "mfa_verified": mfa_verified,
        "iat": now,
        "exp": now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def create_mfa_challenge_token(
    user: User,
) -> str:
    """
    Create a short-lived token used only for MFA verification.
    """

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "purpose": "mfa_challenge",
        "iat": now,
        "exp": now + timedelta(
            minutes=MFA_CHALLENGE_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


# ---------------------------------------------------------
# Registration
# ---------------------------------------------------------


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new Question Setter.
    """

    email = request.email.strip().lower()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        full_name=request.full_name.strip(),
        email=email,
        password_hash=hash_password(request.password),
        role="QUESTION_SETTER",
        is_active=True,
        mfa_enabled=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    create_audit_log(
        db=db,
        user_id=user.id,
        action="USER_REGISTERED",
        resource_type="User",
        resource_id=user.id,
        details=(
            f"New Question Setter account registered "
            f"for email '{user.email}'."
        ),
        ip_address=None,
    )

    return {
        "message": "Account created successfully.",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "mfa_enabled": user.mfa_enabled,
        },
    }


# ---------------------------------------------------------
# Login
# ---------------------------------------------------------


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate using email and password.

    If MFA is enabled, return a short-lived MFA challenge
    instead of the final access token.
    """

    email = request.email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user or not verify_password(
        request.password,
        user.password_hash,
    ):
        create_audit_log(
            db=db,
            user_id=user.id if user else None,
            action="LOGIN_FAILED",
            resource_type="User",
            resource_id=user.id if user else None,
            details=(
                f"Failed password authentication attempt "
                f"for email '{email}'."
            ),
            ip_address=None,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if not user.is_active:

        create_audit_log(
            db=db,
            user_id=user.id,
            action="LOGIN_BLOCKED",
            resource_type="User",
            resource_id=user.id,
            details="Login attempt rejected because the account is inactive.",
            ip_address=None,
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # -----------------------------------------------------
    # MFA required
    # -----------------------------------------------------

    if user.mfa_enabled:

        mfa_token = create_mfa_challenge_token(
            user
        )

        create_audit_log(
            db=db,
            user_id=user.id,
            action="PASSWORD_AUTHENTICATED_MFA_REQUIRED",
            resource_type="User",
            resource_id=user.id,
            details=(
                "Password authentication succeeded. "
                "MFA verification is required."
            ),
            ip_address=None,
        )

        return {
            "message": (
                "Password verified. "
                "MFA verification required."
            ),
            "mfa_required": True,
            "mfa_token": mfa_token,
            "expires_in": (
                MFA_CHALLENGE_EXPIRE_MINUTES * 60
            ),
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
            },
        }

    # -----------------------------------------------------
    # Normal login
    # -----------------------------------------------------

    access_token = create_access_token(
        user,
        mfa_verified=True,
    )

    create_audit_log(
        db=db,
        user_id=user.id,
        action="LOGIN_SUCCESS",
        resource_type="User",
        resource_id=user.id,
        details="User authenticated successfully.",
        ip_address=None,
    )

    return {
        "message": "Login successful.",
        "mfa_required": False,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": (
            ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ),
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
        },
    }


# ---------------------------------------------------------
# MFA Setup
# ---------------------------------------------------------


@router.post("/mfa/setup")
def setup_mfa(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Generate a new TOTP secret.

    The secret is encrypted before being stored.
    """

    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA is already enabled for this account.",
        )

    secret = generate_mfa_secret()

    current_user.mfa_secret = encrypt_mfa_secret(
        secret
    )

    db.commit()

    provisioning_uri = create_provisioning_uri(
        secret,
        current_user.email,
    )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="MFA_SETUP_INITIATED",
        resource_type="User",
        resource_id=current_user.id,
        details="TOTP MFA setup was initiated.",
        ip_address=None,
    )

    return {
        "message": (
            "MFA setup generated. "
            "Add this account to your authenticator app "
            "and verify the generated code."
        ),
        "email": current_user.email,
        "secret": secret,
        "provisioning_uri": provisioning_uri,
    }


# ---------------------------------------------------------
# MFA Enable
# ---------------------------------------------------------


@router.post("/mfa/enable")
def enable_mfa(
    request: MFACodeRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Enable MFA after successful TOTP verification.
    """

    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA is already enabled.",
        )

    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "MFA setup has not been initialized. "
                "Run /auth/mfa/setup first."
            ),
        )

    try:
        secret = decrypt_mfa_secret(
            current_user.mfa_secret
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    if not verify_totp_code(
        secret,
        request.code,
    ):
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="MFA_ENABLE_FAILED",
            resource_type="User",
            resource_id=current_user.id,
            details="Invalid TOTP code supplied while enabling MFA.",
            ip_address=None,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA verification code.",
        )

    current_user.mfa_enabled = True

    db.commit()
    db.refresh(current_user)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="MFA_ENABLED",
        resource_type="User",
        resource_id=current_user.id,
        details="Multi-Factor Authentication was enabled.",
        ip_address=None,
    )

    return {
        "message": (
            "Multi-Factor Authentication "
            "enabled successfully."
        ),
        "mfa_enabled": True,
    }


# ---------------------------------------------------------
# MFA Verification During Login
# ---------------------------------------------------------


@router.post("/mfa/verify")
def verify_mfa(
    request: MFACodeRequest,
    mfa_token: str,
    db: Session = Depends(get_db),
):
    """
    Complete MFA authentication and issue the final JWT.
    """

    try:
        payload = jwt.decode(
            mfa_token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        if payload.get("purpose") != "mfa_challenge":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA challenge token.",
            )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA challenge token.",
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid or expired MFA challenge token."
            ),
        )

    user = (
        db.query(User)
        .filter(User.id == int(user_id))
        .first()
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive.",
        )

    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account.",
        )

    try:
        secret = decrypt_mfa_secret(
            user.mfa_secret
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    if not verify_totp_code(
        secret,
        request.code,
    ):
        create_audit_log(
            db=db,
            user_id=user.id,
            action="MFA_VERIFICATION_FAILED",
            resource_type="User",
            resource_id=user.id,
            details="Invalid TOTP code supplied during login.",
            ip_address=None,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA verification code.",
        )

    access_token = create_access_token(
        user,
        mfa_verified=True,
    )

    create_audit_log(
        db=db,
        user_id=user.id,
        action="MFA_VERIFICATION_SUCCESS",
        resource_type="User",
        resource_id=user.id,
        details=(
            "MFA verification succeeded and an "
            "authenticated access token was issued."
        ),
        ip_address=None,
    )

    return {
        "message": "MFA verification successful.",
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": (
            ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ),
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
        },
    }


# ---------------------------------------------------------
# MFA Disable
# ---------------------------------------------------------


@router.post("/mfa/disable")
def disable_mfa(
    request: MFADisableRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    """
    Disable MFA only after both password and current
    TOTP verification succeed.
    """

    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA is not enabled.",
        )

    if not verify_password(
        request.password,
        current_user.password_hash,
    ):
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="MFA_DISABLE_FAILED",
            resource_type="User",
            resource_id=current_user.id,
            details="Invalid password supplied while disabling MFA.",
            ip_address=None,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password.",
        )

    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA secret is unavailable.",
        )

    try:
        secret = decrypt_mfa_secret(
            current_user.mfa_secret
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    if not verify_totp_code(
        secret,
        request.code,
    ):
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="MFA_DISABLE_FAILED",
            resource_type="User",
            resource_id=current_user.id,
            details="Invalid TOTP code supplied while disabling MFA.",
            ip_address=None,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA verification code.",
        )

    current_user.mfa_enabled = False
    current_user.mfa_secret = None

    db.commit()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="MFA_DISABLED",
        resource_type="User",
        resource_id=current_user.id,
        details="Multi-Factor Authentication was disabled.",
        ip_address=None,
    )

    return {
        "message": (
            "Multi-Factor Authentication disabled."
        ),
        "mfa_enabled": False,
    }