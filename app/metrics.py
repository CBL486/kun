"""Minimal Prometheus-compatible runtime metrics."""

from __future__ import annotations

import threading
import time


class MetricsRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._requests = 0
        self._errors = 0
        self._duration_sum = 0.0

    def observe(self, *, status_code: int, duration_seconds: float) -> None:
        with self._lock:
            self._requests += 1
            if status_code >= 500:
                self._errors += 1
            self._duration_sum += max(0.0, duration_seconds)

    def render(
        self,
        *,
        version: str,
        database_ready: bool,
        scheduler_backlog: dict[str, int] | None,
        backup_age_seconds: float | None = None,
    ) -> str:
        with self._lock:
            requests = self._requests
            errors = self._errors
            duration_sum = self._duration_sum
        lines = [
            "# HELP aiworld_up Process liveness indicator.",
            "# TYPE aiworld_up gauge",
            "aiworld_up 1",
            "# HELP aiworld_database_ready Database readiness.",
            "# TYPE aiworld_database_ready gauge",
            f"aiworld_database_ready {1 if database_ready else 0}",
            "# HELP aiworld_app_info Application version.",
            "# TYPE aiworld_app_info gauge",
            f'aiworld_app_info{{version="{_escape(version)}"}} 1',
            "# HELP aiworld_http_requests_total HTTP requests observed.",
            "# TYPE aiworld_http_requests_total counter",
            f"aiworld_http_requests_total {requests}",
            "# HELP aiworld_http_errors_total HTTP 5xx responses.",
            "# TYPE aiworld_http_errors_total counter",
            f"aiworld_http_errors_total {errors}",
            "# HELP aiworld_http_request_duration_seconds_sum Summed request time.",
            "# TYPE aiworld_http_request_duration_seconds_sum counter",
            f"aiworld_http_request_duration_seconds_sum {duration_sum:.6f}",
            "# HELP aiworld_http_request_duration_seconds_count Request count.",
            "# TYPE aiworld_http_request_duration_seconds_count counter",
            f"aiworld_http_request_duration_seconds_count {requests}",
            "# HELP aiworld_process_start_time_seconds Process start time.",
            "# TYPE aiworld_process_start_time_seconds gauge",
            f"aiworld_process_start_time_seconds {self._started_at:.3f}",
            "# HELP aiworld_scheduler_database_configured Scheduler DB configured.",
            "# TYPE aiworld_scheduler_database_configured gauge",
            f"aiworld_scheduler_database_configured {1 if scheduler_backlog is not None else 0}",
        ]
        if scheduler_backlog is not None:
            lines.extend(
                [
                    "# HELP aiworld_scheduler_pending_due Due pending tasks.",
                    "# TYPE aiworld_scheduler_pending_due gauge",
                    f"aiworld_scheduler_pending_due {scheduler_backlog['pending_due']}",
                    "# HELP aiworld_scheduler_delayed Delayed tasks.",
                    "# TYPE aiworld_scheduler_delayed gauge",
                    f"aiworld_scheduler_delayed {scheduler_backlog['delayed']}",
                    "# HELP aiworld_scheduler_leased Leased tasks.",
                    "# TYPE aiworld_scheduler_leased gauge",
                    f"aiworld_scheduler_leased {scheduler_backlog['leased']}",
                    "# HELP aiworld_scheduler_expired_leases Expired leases.",
                    "# TYPE aiworld_scheduler_expired_leases gauge",
                    f"aiworld_scheduler_expired_leases {scheduler_backlog['expired_leases']}",
                ]
            )
        if backup_age_seconds is not None:
            lines.extend(
                [
                    "# HELP aiworld_backup_age_seconds Age of newest database backup.",
                    "# TYPE aiworld_backup_age_seconds gauge",
                    f"aiworld_backup_age_seconds {backup_age_seconds:.3f}",
                ]
            )
        return "\n".join(lines) + "\n"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
