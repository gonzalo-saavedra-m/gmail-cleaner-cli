from __future__ import annotations

from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from libs.env_loader import env


DEFAULT_REFRESH_TOKEN_PATH = ".secrets/google_refresh_token.enc"


def generate_encryption_key() -> str:
    """Create a new Fernet key for encrypting local token files."""
    return Fernet.generate_key().decode("utf-8")


def has_encryption_key() -> bool:
    """Return whether a usable token encryption key is configured."""
    key = env("TOKEN_ENCRYPTION_KEY", required=False)
    return bool(key and key != "your-generated-encryption-key")


def refresh_token_path() -> Path:
    """Return the configured path for the encrypted Gmail refresh token."""
    return Path(env("GOOGLE_REFRESH_TOKEN_FILE", required=False, default=DEFAULT_REFRESH_TOKEN_PATH))


def has_refresh_token() -> bool:
    """Return whether the encrypted Gmail refresh token file exists."""
    return refresh_token_path().exists()


def cipher() -> Fernet:
    """Create the Fernet cipher from TOKEN_ENCRYPTION_KEY."""
    key = env("TOKEN_ENCRYPTION_KEY")
    return Fernet(key.encode("utf-8"))


def save_refresh_token(refresh_token: str) -> Path:
    """Encrypt and write the Gmail refresh token to the configured token file."""
    path = refresh_token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    encrypted_token = cipher().encrypt(refresh_token.encode("utf-8"))
    path.write_bytes(encrypted_token)
    return path


def load_refresh_token() -> str:
    """Decrypt and return the stored Gmail refresh token."""
    path = refresh_token_path()

    if not path.exists():
        raise SystemExit(
            f"Missing encrypted refresh token file: {path}\n"
            "Choose option 1 from the main menu to connect a Gmail account."
        )

    try:
        return cipher().decrypt(path.read_bytes()).decode("utf-8")
    except InvalidToken as error:
        raise SystemExit(
            "Could not decrypt the refresh token. Check TOKEN_ENCRYPTION_KEY in .env."
        ) from error
