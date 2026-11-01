"""Small deterministic circuit breaker for model providers."""

from __future__ import annotations

import time
from typing import Callable

from .models import CircuitState


class CircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int = 2,
        cooldown_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.clock = clock
        self.state = CircuitState()

    def allow(self) -> bool:
        if not self.state.open:
            return True
        opened_at = self.state.opened_at or 0.0
        return self.clock() - opened_at >= self.cooldown_seconds

    def record_success(self) -> None:
        self.state = CircuitState()

    def record_failure(self) -> None:
        failures = self.state.consecutive_failures + 1
        opened = failures >= self.failure_threshold
        self.state = CircuitState(
            open=opened,
            consecutive_failures=failures,
            opened_at=self.clock() if opened else self.state.opened_at,
        )
