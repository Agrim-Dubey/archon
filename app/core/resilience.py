"""Circuit Breaker pattern implementation with fallbacks and resilience policies."""

from enum import Enum
import time
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted while circuit is open."""
    pass


class CircuitBreaker:
    """Circuit breaker with state tracking, half-open trial, and fallbacks."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_time_seconds: float = 30.0,
        half_open_success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.half_open_success_threshold = half_open_success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()

    def _update_state(self) -> None:
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_state_change >= self.recovery_time_seconds:
                logger.info("Circuit %s transitioning from OPEN to HALF_OPEN", self.name)
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.last_state_change = now

    async def call(
        self,
        func: Callable,
        *args,
        fallback: Optional[Callable] = None,
        **kwargs,
    ) -> Any:
        """Execute callable protected by the circuit breaker."""
        self._update_state()

        if self.state == CircuitState.OPEN:
            logger.warning("Circuit %s is OPEN. Invoking fallback if available.", self.name)
            if fallback:
                return await fallback(*args, **kwargs) if callable(fallback) else fallback
            raise CircuitBreakerOpenException(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            if fallback:
                logger.info("Function failed under circuit %s. Invoking fallback.", self.name)
                return await fallback(*args, **kwargs) if callable(fallback) else fallback
            raise e

    def _on_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_success_threshold:
                logger.info("Circuit %s recovering: HALF_OPEN -> CLOSED", self.name)
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_state_change = time.time()
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            logger.error(
                "Circuit %s tripping: %s -> OPEN (Failures: %d)",
                self.name,
                self.state,
                self.failure_count,
            )
            self.state = CircuitState.OPEN
