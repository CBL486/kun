"""导出 B6 静态 OpenAPI 契约。"""

from __future__ import annotations

import json
from pathlib import Path

from app.main import app


def main() -> int:
    output = Path(__file__).resolve().parents[1] / "docs" / "openapi-v1.json"
    output.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
