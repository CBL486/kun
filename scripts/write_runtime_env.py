from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import quote


SECRET_PATH = Path(r"C:\AIWorld\data\secrets\aiworld_database_password.txt")
DEEPSEEK_KEY_PATH = Path(r"C:\AIWorld\data\secrets\deepseek_api_key.txt")
ENV_PATH = Path(r"C:\AIWorld\app\.env")


def main() -> None:
    password = quote(SECRET_PATH.read_text(encoding="utf-8").strip(), safe="")
    if not DEEPSEEK_KEY_PATH.is_file():
        raise FileNotFoundError(
            f"DeepSeek API key file not found: {DEEPSEEK_KEY_PATH}"
        )
    raw_deepseek_key = DEEPSEEK_KEY_PATH.read_text(encoding="utf-8").strip()
    if not raw_deepseek_key:
        raise ValueError(f"DeepSeek API key file is empty: {DEEPSEEK_KEY_PATH}")
    deepseek_key = raw_deepseek_key
    content = "\n".join(
        (
            "AIWORLD_ENVIRONMENT=production",
            f"AIWORLD_DATABASE_URL=postgresql+asyncpg://aiworld:{password}@127.0.0.1:55432/aiworld",
            "AIWORLD_LOG_LEVEL=INFO",
            "AIWORLD_LLM_PROVIDER=deepseek",
            "AIWORLD_LLM_BASE_URL=https://api.deepseek.com",
            "AIWORLD_LLM_MODEL=deepseek-flash",
            f"AIWORLD_LLM_API_KEY={deepseek_key}",
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
            "Administrator:(R,W)",
            "SYSTEM:(R,W)",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    print(f"ENV_OK path={ENV_PATH} database=aiworld@127.0.0.1:55432")


if __name__ == "__main__":
    main()
