"""Run requeststoken.org.

    uv run python app.py
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from requeststoken.web import create_app

ROOT = Path(__file__).resolve().parent


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines into the environment without overriding real vars."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


load_env_file(ROOT / ".env")

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

api = create_app()


if __name__ == "__main__":
    port = int(os.environ["PORT"]) if os.environ.get("PORT") else 5042
    api.run(address="0.0.0.0", port=port)
