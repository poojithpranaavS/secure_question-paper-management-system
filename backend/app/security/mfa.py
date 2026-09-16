import base64
import os

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv


load_dotenv()


MFA_ENCRYPTION_KEY_ENV = "MFA_ENCRYPTION_KEY"


def get_mfa_cipher() -> Fernet:
    """
    Return the Fernet cipher used to encrypt stored MFA secrets.
    """

    encoded_key = os.getenv(MFA_ENCRYPTION_KEY_ENV)

    if not encoded_key:
        raise RuntimeError(
            f"{MFA_ENCRYPTION_KEY_ENV} is not configured."
        )

    try:
        key = base64.urlsafe_b64decode(
            encoded_key.encode("utf-8")
        )

        if len(key) != 32:
            raise ValueError

    except Exception as exc:
        raise RuntimeError(
            "Invalid MFA encryption key."
        ) from exc

    return Fernet(
        base64.urlsafe_b64encode(key)
    )


def encrypt_mfa_secret(secret: str) -> str:
    """
    Encrypt a TOTP secret before storing it in the database.
    """

    cipher = get_mfa_cipher()

    encrypted = cipher.encrypt(
        secret.encode("utf-8")
    )

    return encrypted.decode("utf-8")


def decrypt_mfa_secret(encrypted_secret: str) -> str:
    """
    Decrypt a stored TOTP secret.
    """

    cipher = get_mfa_cipher()

    try:
        decrypted = cipher.decrypt(
            encrypted_secret.encode("utf-8")
        )

    except InvalidToken as exc:
        raise RuntimeError(
            "Unable to decrypt MFA secret."
        ) from exc

    return decrypted.decode("utf-8")


def generate_mfa_secret() -> str:
    """
    Generate a cryptographically random TOTP secret.
    """

    return pyotp.random_base32()


def verify_totp_code(
    secret: str,
    code: str,
) -> bool:
    """
    Verify a six-digit TOTP code.

    A small time window is allowed to account for
    clock differences between the server and authenticator.
    """

    if not code or not code.isdigit():
        return False

    if len(code) != 6:
        return False

    totp = pyotp.TOTP(secret)

    return totp.verify(
        code,
        valid_window=1,
    )


def create_provisioning_uri(
    secret: str,
    email: str,
) -> str:
    """
    Create an otpauth URI compatible with authenticator apps.
    """

    totp = pyotp.TOTP(secret)

    return totp.provisioning_uri(
        name=email,
        issuer_name="Secure Question Paper Management System",
    )