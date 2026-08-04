from dataclasses import dataclass, field


@dataclass
class RequestCounters:
    """In-memory, process-local counters - reset on restart, not persisted,
    not exposed via any endpoint (periodically logged instead, per project
    decision). Tracks running aggregates (count/sum/min/max), not individual
    samples, so memory use stays flat regardless of how long the process runs.
    """

    total_requests: int = 0
    status_class_counts: dict[str, int] = field(default_factory=dict)
    redirect_count: int = 0
    redirect_latency_sum_ms: float = 0.0
    redirect_latency_min_ms: float | None = None
    redirect_latency_max_ms: float | None = None

    def record(self, status_code: int, duration_ms: float, is_redirect: bool) -> None:
        self.total_requests += 1
        status_class = f"{status_code // 100}xx"
        self.status_class_counts[status_class] = self.status_class_counts.get(status_class, 0) + 1

        if is_redirect:
            self.redirect_count += 1
            self.redirect_latency_sum_ms += duration_ms
            if self.redirect_latency_min_ms is None or duration_ms < self.redirect_latency_min_ms:
                self.redirect_latency_min_ms = duration_ms
            if self.redirect_latency_max_ms is None or duration_ms > self.redirect_latency_max_ms:
                self.redirect_latency_max_ms = duration_ms

    def summary(self) -> dict:
        error_count = sum(
            count
            for status_class, count in self.status_class_counts.items()
            if status_class in ("4xx", "5xx")
        )
        error_rate = error_count / self.total_requests if self.total_requests else 0.0
        avg_latency_ms = (
            self.redirect_latency_sum_ms / self.redirect_count if self.redirect_count else None
        )
        return {
            "total_requests": self.total_requests,
            "status_class_counts": dict(self.status_class_counts),
            "error_rate": round(error_rate, 4),
            "redirect_count": self.redirect_count,
            "redirect_avg_latency_ms": round(avg_latency_ms, 2)
            if avg_latency_ms is not None
            else None,
            "redirect_min_latency_ms": self.redirect_latency_min_ms,
            "redirect_max_latency_ms": self.redirect_latency_max_ms,
        }


_counters = RequestCounters()


def get_counters() -> RequestCounters:
    return _counters


def reset_counters() -> None:
    """Process-wide singleton state - tests need to reset between runs to
    avoid cross-test contamination of counts."""
    global _counters
    _counters = RequestCounters()
