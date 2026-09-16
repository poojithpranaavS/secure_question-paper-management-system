import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


KEY_ENV_NAME = "QUESTION_PAPER_ENCRYPTION_KEY"


def get_encryption_key() -> bytes:
    """
    Load the AES-256 encryption key from the environment.
    """

    encoded_key = os.getenv(KEY_ENV_NAME)

    if not encoded_key:
        raise RuntimeError(
            f"{KEY_ENV_NAME} is not configured."
        )

    try:
        key = base64.urlsafe_b64decode(encoded_key)
    except Exception as exc:
        raise RuntimeError(
            "Invalid question-paper encryption key."
        ) from exc

    if len(key) != 32:
        raise RuntimeError(
            "Question-paper encryption key must be 32 bytes "
            "(256 bits)."
        )

    return key


def encrypt_file(data: bytes) -> bytes:
    """
    Encrypt file contents using AES-256-GCM.

    The returned data contains:
        nonce + encrypted ciphertext + authentication tag
    """

    key = get_encryption_key()

    aes_gcm = AESGCM(key)

    nonce = os.urandom(12)

    encrypted_data = aes_gcm.encrypt(
        nonce,
        data,
        None,
    )

    return nonce + encrypted_data


def decrypt_file(encrypted_data: bytes) -> bytes:
    """
    Decrypt AES-256-GCM encrypted file contents.
    """

    key = get_encryption_key()

    if len(encrypted_data) < 13:
        raise ValueError(
            "Invalid encrypted file."
        )

    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]

    aes_gcm = AESGCM(key)

    return aes_gcm.decrypt(
        nonce,
        ciphertext,
        None,
    )