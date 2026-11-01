"""Allowlisted release packaging with checksums and secret-file exclusion."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from rpg_orm.migrations import LATEST_SCHEMA_VERSION


INCLUDE_DIRS = (
    "app",
    "memory_core",
    "rpg_agent",
    "rpg_llm",
    "rpg_npc",
    "rpg_orm",
    "rpg_quality",
    "rpg_scheduler",
    "rpg_sim",
    "rpg_storage",
    "rpg_stress",
    "agent_core",
    "world_engine",
    "narrative_director",
    "npc_runtime",
    "web",
    "assets",
    "content",
    "deploy",
)
INCLUDE_FILES = (
    "README.md",
    "pyproject.toml",
    "requirements-b5.txt",
    "requirements-b6.txt",
    "docs/deployment-checklist.md",
    "docs/rollback-runbook.md",
    "docs/deployment-topology-v1.md",
    "docs/asset-license-audit.md",
    "docs/scheduler-recovery-v1.md",
    "docs/llm-gateway-v1.md",
    "docs/security-failure-matrix-v1.md",
)
EXCLUDED_PARTS = {
    ".git",
    ".env",
    ".venv",
    ".b5-deps",
    ".b6-deps",
    ".pytest_cache",
    "__pycache__",
    "data",
    "logs",
    "backups",
    "out",
    "tmp",
}
FORBIDDEN_SUFFIXES = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".key",
    ".pem",
    ".p12",
    ".zip",
    ".rar",
    ".7z",
    ".psd",
    ".aseprite",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_version(root: Path) -> str:
    import tomllib

    payload = tomllib.loads((root / "pyproject.toml").read_text("utf-8"))
    return str(payload["project"]["version"])


def _commit(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        encoding="utf-8",
    ).strip()


def _release_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory in INCLUDE_DIRS:
        base = root / directory
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            if path.suffix.lower() in FORBIDDEN_SUFFIXES:
                continue
            files.append(path)
    for relative in INCLUDE_FILES:
        path = root / relative
        if path.is_file():
            files.append(path)
    return sorted(set(files), key=lambda path: path.as_posix())


def build_release(
    root: Path,
    output: Path,
    *,
    version: str | None = None,
    built_at: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"发布目录已存在：{output}")
    release_version = version or _project_version(root)
    commit = _commit(root)
    created = built_at or datetime.now(timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    entries = []
    for source in _release_files(root):
        relative = source.relative_to(root)
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        entries.append(
            {
                "path": relative.as_posix(),
                "bytes": target.stat().st_size,
                "sha256": _sha256(target),
            }
        )
    checksums = "".join(
        f"{entry['sha256']}  {entry['path']}\n" for entry in entries
    )
    manifest = {
        "schema_version": "rpg-release-manifest-v1",
        "version": release_version,
        "git_commit": commit,
        "database_schema_version": LATEST_SCHEMA_VERSION,
        "built_at": created,
        "files": entries,
        "package_sha256": hashlib.sha256(
            checksums.encode("utf-8")
        ).hexdigest(),
    }
    manifest_text = json.dumps(
        manifest,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    (output / "RELEASE_MANIFEST.json").write_text(
        manifest_text,
        encoding="utf-8",
        newline="\n",
    )
    (output / "checksums.sha256").write_text(
        checksums,
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def verify_release(release: Path) -> list[str]:
    release = release.resolve()
    manifest_path = release / "RELEASE_MANIFEST.json"
    if not manifest_path.is_file():
        return ["RELEASE_MANIFEST.json missing"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ["RELEASE_MANIFEST.json invalid"]
    issues = []
    listed = set()
    for entry in manifest.get("files", []):
        relative = entry["path"]
        listed.add(relative)
        path = release / relative
        if not path.is_file():
            issues.append(f"missing:{relative}")
            continue
        if path.stat().st_size != entry["bytes"]:
            issues.append(f"size:{relative}")
        if _sha256(path) != entry["sha256"]:
            issues.append(f"sha256:{relative}")
        if _forbidden_release_path(Path(relative)):
            issues.append(f"forbidden:{relative}")
    actual = {
        path.relative_to(release).as_posix()
        for path in release.rglob("*")
        if path.is_file()
        and path.name not in {"RELEASE_MANIFEST.json", "checksums.sha256"}
    }
    for unexpected in sorted(actual - listed):
        issues.append(f"unlisted:{unexpected}")
    checksum_path = release / "checksums.sha256"
    if not checksum_path.is_file():
        issues.append("checksums.sha256 missing")
    else:
        checksum_bytes = checksum_path.read_bytes()
        expected_package_hash = hashlib.sha256(checksum_bytes).hexdigest()
        if manifest.get("package_sha256") != expected_package_hash:
            issues.append("package_sha256")
    return issues


def _forbidden_release_path(path: Path) -> bool:
    return (
        any(part in EXCLUDED_PARTS for part in path.parts)
        or path.suffix.lower() in FORBIDDEN_SUFFIXES
    )


def validate_template_directory(root: Path) -> list[str]:
    issues = []
    nginx = root / "deploy" / "reverse-proxy" / "nginx.conf.template"
    caddy = root / "deploy" / "reverse-proxy" / "Caddyfile.template"
    prometheus = root / "deploy" / "monitoring" / "prometheus.yml"
    alerts = root / "deploy" / "monitoring" / "alerts.yml"
    required = {
        nginx: ("__DOMAIN__", "location = /metrics", "limit_req"),
        caddy: ("{$AIWORLD_DOMAIN}", "reverse_proxy 127.0.0.1:8080", "@metrics"),
        prometheus: ("127.0.0.1:8080", "metrics_path: /metrics"),
        alerts: ("AIWorldDatabaseNotReady", "AIWorldSchedulerExpiredLeases"),
    }
    for path, needles in required.items():
        if not path.is_file():
            issues.append(f"missing:{path.relative_to(root).as_posix()}")
            continue
        content = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in content:
                issues.append(
                    f"template:{path.relative_to(root).as_posix()}:{needle}"
                )
        if path.suffix == ".template":
            if content.count("{") != content.count("}"):
                issues.append(
                    f"template_braces:{path.relative_to(root).as_posix()}"
                )
    return issues
