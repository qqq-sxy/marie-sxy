"""Load API keys and options from local ``.env`` files (never committed to git)."""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv_files() -> None:
    """Populate ``os.environ`` from dotenv files.

    Precedence (later calls do not override existing vars unless noted):

    1. ``MARIE_SXY_ENV_FILE`` — explicit path to a single ``.env`` file.
    2. ``<cwd>/.env`` — project-local secrets when you run the CLI from that directory.
    3. ``$XDG_CONFIG_HOME/marie_sxy/.env`` or ``~/.config/marie_sxy/.env`` — user-wide fallback.

    Shell-exported variables always win (``override=False``).
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    explicit = os.environ.get("MARIE_SXY_ENV_FILE")
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if path.is_file():
            load_dotenv(path, override=False)
        return

    cwd_env = Path.cwd() / ".env"
    if cwd_env.is_file():
        load_dotenv(cwd_env, override=False)

    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    user_env = base / "marie_sxy" / ".env"
    if user_env.is_file():
        load_dotenv(user_env, override=False)
