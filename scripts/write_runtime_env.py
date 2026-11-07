from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import quote


SECRET_PATH = Path(r"C:\AIWorld\data\secrets\aiworld_database_password.txt")
DEEPSEEK_KEY_PATH = Path(r"C:\AIWorld\data\setup\deepseek_api_key.txt")
ENV_PATH = Path(r"C:\AIWorld\config\production.env")


def main() -> None:
    password = quote(SECRET_PATH.read_text(encoding="utf-8").strip(), safe="")
    if not DEEPSEEK_KEY_PATH.is_file():
        raise FileNotFoundError(
            f"DeepSeek API key file not found: {DEEPSEEK_KEY_PATH}"
        )
    if not DEEPSEEK_KEY_PATH.read_text(encoding="utf-8").strip():
        raise ValueError(f"DeepSeek API key file is empty: {DEEPSEEK_KEY_PATH}")
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        (
            "AIWORLD_ENVIRONMENT=production",
            f"AIWORLD_DATABASE_URL=postgresql+asyncpg://aiworld:{password}@127.0.0.1:55432/aiworld",
            f"AIWORLD_SCHEDULER_DATABASE_URL=postgresql+psycopg://aiworld:{password}@127.0.0.1:55432/aiworld",
            f"AIWORLD_PRODUCT_DATABASE_URL=postgresql+psycopg://aiworld:{password}@127.0.0.1:55432/aiworld",
            f"AIWORLD_BACKUP_DATABASE_URL=postgresql+psycopg://aiworld:{password}@127.0.0.1:55432/aiworld",
            "AIWORLD_BACKUP_DIRECTORY=C:/AIWorld/backups",
            "AIWORLD_SETUP_DIRECTORY=C:\\AIWorld\\data\\setup",
            "AIWORLD_PERSONA_DIRECTORY=C:\\AIWorld\\data\\persona",
            "AIWORLD_WORLD_CLOCK_DIRECTORY=C:\\AIWorld\\data\\world",
            "AIWORLD_ENFORCE_SETUP_ACL=true",
            "AIWORLD_WORLD_TICK_MINUTES=10",
            "AIWORLD_LOG_LEVEL=INFO",
            "AIWORLD_LLM_PROVIDER=deepseek",
            "AIWORLD_LLM_BASE_URL=https://api.deepseek.com",
            "AIWORLD_LLM_MODEL=deepseek-flash",
            f"AIWORLD_LLM_API_KEY_FILE={DEEPSEEK_KEY_PATH}",
            "AIWORLD_LLM_REVIEW_PROVIDER=local",
            "AIWORLD_LLM_PRICE_VERSION=deepseek-flash-peak-cny-2026-11-02",
            "AIWORLD_LLM_MAX_COST_CNY=0.10",
            "",
        )
    )
    ENV_PATH.write_text(content, encoding="utf-8", newline="\n")
    subprocess.run(
        [
            "icacls",
            str(ENV_PATH),
            "/inheritance:r",
            "/grant:r",
            "*S-1-5-32-544:(R,W)",
            "*S-1-5-18:(R,W)",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    print(f"ENV_OK path={ENV_PATH} database=aiworld@127.0.0.1:55432")


if __name__ == "__main__":
    main()
