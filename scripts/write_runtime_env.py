from __future__ import annotations

import subprocess
from pathlib import Path
from urllib.parse import quote


SECRET_PATH = Path(r"C:\AIWorld\data\secrets\aiworld_database_password.txt")
ENV_PATH = Path(r"C:\AIWorld\app\.env")


def main() -> None:
    password = quote(SECRET_PATH.read_text(encoding="utf-8").strip(), safe="")
    content = "\n".join(
        (
            "AIWORLD_ENVIRONMENT=production",
            f"AIWORLD_DATABASE_URL=postgresql+asyncpg://aiworld:{password}@127.0.0.1:55432/aiworld",
            "AIWORLD_LOG_LEVEL=INFO",
            "AIWORLD_LLM_MODEL=deepseek-chat",
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
