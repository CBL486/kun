"""Command-line release builder and verifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .release import build_release, validate_template_directory, verify_release


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="B12 release packaging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build")
    build.add_argument("--output", required=True)
    build.add_argument("--version")
    build.add_argument("--built-at")

    verify = subparsers.add_parser("verify")
    verify.add_argument("--release", required=True)

    subparsers.add_parser("config-check")

    args = parser.parse_args()
    if args.command == "build":
        manifest = build_release(
            ROOT,
            Path(args.output),
            version=args.version,
            built_at=args.built_at,
        )
        print(
            json.dumps(
                {
                    "version": manifest["version"],
                    "git_commit": manifest["git_commit"],
                    "files": len(manifest["files"]),
                    "package_sha256": manifest["package_sha256"],
                },
                ensure_ascii=False,
            )
        )
        return 0
    if args.command == "verify":
        issues = verify_release(Path(args.release))
        print(json.dumps({"issues": issues}, ensure_ascii=False))
        return 0 if not issues else 1
    issues = validate_template_directory(ROOT)
    print(json.dumps({"issues": issues}, ensure_ascii=False))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
