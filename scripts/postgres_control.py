from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from embedded_postgres._commands import pg_ctl, pg_isready


DEFAULT_PGDATA = Path(os.environ.get("AIWORLD_PGDATA", r"C:\AIWorld\data\postgres"))
DEFAULT_HOST = os.environ.get("AIWORLD_PGHOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("AIWORLD_PGPORT", "55432"))


def configure_instance(pgdata: Path, host: str, port: int) -> None:
    """Pin the project instance to a deterministic local endpoint."""
    config_path = pgdata / "postgresql.conf"
    lines = [
        line
        for line in config_path.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith(("listen_addresses", "port"))
    ]
    lines.extend((f"listen_addresses = '{host}'", f"port = {port}"))
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def is_ready(pgdata: Path, host: str, port: int) -> bool:
    """Return whether the configured PostgreSQL endpoint accepts connections."""
    if not (pgdata / "PG_VERSION").exists():
        return False
    try:
        pg_isready(["-h", host, "-p", str(port)], timeout=5)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
    return True


def start(pgdata: Path, host: str, port: int) -> None:
    """Start the project-owned PostgreSQL instance on a fixed local endpoint."""
    if not (pgdata / "PG_VERSION").exists():
        raise SystemExit(f"PGDATA is not initialized: {pgdata}")
    configure_instance(pgdata, host, port)
    if is_ready(pgdata, host, port):
        print(f"PostgreSQL already ready at {host}:{port}")
        return

    log_path = pgdata / "server.log"
    pg_ctl(
        ["-w", "-l", str(log_path), "start"],
        pgdata=pgdata,
        timeout=30,
    )
    if not is_ready(pgdata, host, port):
        raise SystemExit(f"PostgreSQL did not become ready; inspect {log_path}")
    print(f"PostgreSQL ready at {host}:{port}")


def stop(pgdata: Path, host: str, port: int) -> None:
    """Fast-stop the project-owned PostgreSQL instance."""
    if not is_ready(pgdata, host, port):
        print("PostgreSQL is not running")
        return
    pg_ctl(["-w", "stop", "-m", "fast"], pgdata=pgdata, timeout=30)
    print("PostgreSQL stopped")


def status(pgdata: Path, host: str, port: int) -> None:
    """Print readiness without changing server state."""
    state = "ready" if is_ready(pgdata, host, port) else "not-ready"
    print(f"PostgreSQL {state} at {host}:{port} (pgdata={pgdata})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Control the AI World PostgreSQL instance")
    parser.add_argument("action", choices=("start", "stop", "status"))
    parser.add_argument("--pgdata", type=Path, default=DEFAULT_PGDATA)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    if args.action == "start":
        start(args.pgdata, args.host, args.port)
    elif args.action == "stop":
        stop(args.pgdata, args.host, args.port)
    else:
        status(args.pgdata, args.host, args.port)


if __name__ == "__main__":
    main()
