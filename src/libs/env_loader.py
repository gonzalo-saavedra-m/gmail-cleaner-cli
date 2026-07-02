from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: Path) -> None:
    """Load KEY=value pairs from a .env file into the process environment."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env(name: str, required: bool = True, default: str | None = None) -> str:
    """Read an environment value, optionally failing when it is missing."""
    value = os.environ.get(name, default)
    if required and not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value or ""


def update_dotenv_value(path: Path, key: str, value: str) -> None:
    """Insert or replace a single KEY=value entry in a .env file."""
    line = f"{key}={value}"

    if not path.exists():
        path.write_text(f"{line}\n", encoding="utf-8")
        os.environ[key] = value
        return

    lines = path.read_text(encoding="utf-8").splitlines()
    updated = False

    for index, existing_line in enumerate(lines):
        if existing_line.strip().startswith(f"{key}="):
            lines[index] = line
            updated = True
            break

    if not updated:
        lines.append(line)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[key] = value
