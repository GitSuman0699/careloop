"""Clock service — real and simulated clocks for CareLoop."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Abstract clock interface."""

    def now(self) -> datetime: ...

    def advance(self, *, days: int = 0, hours: int = 0, minutes: int = 0) -> datetime: ...


class RealClock:
    """Clock backed by the system wall clock (UTC)."""

    def now(self) -> datetime:
        return datetime.utcnow()

    def advance(self, *, days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
        raise NotImplementedError("Cannot advance real clock")


class SimulatedClock:
    """Deterministic clock for simulation and testing.

    Starts at *base* and moves forward only when ``advance()`` is called.
    """

    DEFAULT_BASE = datetime(2026, 1, 15, 8, 0, 0)

    def __init__(self, base: datetime | None = None) -> None:
        self._base = base or self.DEFAULT_BASE
        self._offset = timedelta()

    def now(self) -> datetime:
        return self._base + self._offset

    def advance(self, *, days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
        self._offset += timedelta(days=days, hours=hours, minutes=minutes)
        return self.now()

    def reset(self, base: datetime | None = None) -> None:
        """Reset the clock to *base* (or the original base) with zero offset."""
        self._base = base or self.DEFAULT_BASE
        self._offset = timedelta()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_clock_instance: Clock | None = None


def get_clock() -> Clock:
    """Return the singleton clock instance.

    The clock type is controlled by the ``CLOCK_MODE`` environment variable:
    * ``simulated`` → :class:`SimulatedClock`
    * anything else  → :class:`RealClock`
    """
    global _clock_instance
    if _clock_instance is None:
        mode = os.environ.get("CLOCK_MODE", "real").lower()
        if mode == "simulated":
            _clock_instance = SimulatedClock()
        else:
            _clock_instance = RealClock()
    return _clock_instance


def _reset_clock() -> None:
    """Reset the singleton — for tests only."""
    global _clock_instance
    _clock_instance = None
