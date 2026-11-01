"""Final release evidence without secrets or private runtime data."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

from rpg_orm.migrations import LATEST_SCHEMA_VERSION


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_release_evidence(root: Path) -> dict[str, Any]:
    root = root.resolve()
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).strip()
    tree = subprocess.check_output(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).strip()
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).strip()
    manifest = json.loads(
        (root / "assets" / "manifest.json").read_text(encoding="utf-8")
    )
    e2e = json.loads(
        (root / "docs" / "e2e-7day-summary.json").read_text(encoding="utf-8")
    )
    cost = json.loads(
        (root / "docs" / "b11-cost-report.json").read_text(encoding="utf-8")
    )
    evidence_files = [
        "docs/e2e-7day-summary.json",
        "docs/b11-cost-report.json",
        "docs/art-budget-b7-5.json",
        "docs/asset-license-audit.md",
        "assets/manifest.json",
    ]
    return {
        "schema_version": "rpg-release-evidence-v1",
        "branch": branch,
        "commit": commit,
        "tree": tree,
        "database_schema_version": LATEST_SCHEMA_VERSION,
        "python": platform.python_version(),
        "e2e": {
            "status": e2e["status"],
            "days": e2e["days"],
            "business_hash": e2e["business_hash"],
            "simulation_hash": e2e["simulation_hash"],
            "errors": e2e["quality"]["error_count"],
            "warnings": e2e["quality"]["warning_count"],
        },
        "cost": {
            "bill_matches": cost["bill_matches"],
            "price_versions": cost["price_versions"],
        },
        "assets": {
            "asset_count": len(manifest["assets"]),
            "source_pack_count": len(manifest["source_packs"]),
            "authorized": all(
                asset["license_status"]
                in {"project-authorized", "commercial-licensed"}
                for asset in manifest["assets"]
            ),
        },
        "files": {
            relative: _sha256(root / relative)
            for relative in evidence_files
        },
        "known_risks": [
            "真实供应商价格、审核 SLA 与幂等能力需 staging 确认",
            "Spine Trial 导出需在发布前替换正式许可证版本",
            "四名 NPC 尚无独立 Spine 行走模型",
            "生产环境、TLS、DNS、数据库和备份恢复由 A 执行",
        ],
    }
