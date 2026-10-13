"""F1 / step 2: anti-flood. One customer can't send more than N messages per window.
Sliding window kept in memory (fine for one instance; use Redis if the AI service is ever scaled out)."""
import time
from collections import deque
from typing import Callable


class Throttled(Exception):
    def __init__(self, retry_after: float):
        super().__init__(f"rate limited, retry in {retry_after:.1f}s")
        self.retry_after = retry_after


class SlidingWindowThrottle:
    def __init__(self, max_messages: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self._max, self._window, self._clock = max_messages, window_seconds, clock
        self._hits: dict[str, deque[float]] = {}

    def hit(self, key: str) -> float | None:
        """Register a message. Returns None if allowed, or seconds to wait if the customer is over the limit."""
        now = self._clock()
        q = self._hits.setdefault(key, deque())
        while q and now - q[0] >= self._window:
            q.popleft()
        if len(q) >= self._max:
            return max(self._window - (now - q[0]), 0.001)   # blocked hits are NOT counted
        q.append(now)
        if len(self._hits) > 1000:
            self._prune(now)
        return None

    def _prune(self, now: float) -> None:
        for k in [k for k, q in self._hits.items() if not q or now - q[-1] >= self._window]:
            del self._hits[k]


def throttle_key(business: dict, customer: dict) -> str | None:
    who = customer.get("id") or customer.get("phone")
    return f"{business.get('id', '')}:{who}" if who else None   # unknown customer -> can't throttle
