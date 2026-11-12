"""Tests for the SimulatedClock and RealClock."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.core.clock import RealClock, SimulatedClock


class TestSimulatedClock:
    def test_simulated_clock_starts_at_base(self):
        """Clock.now() returns the base datetime before any advance."""
        base = datetime(2026, 1, 15, 8, 0, 0)
        clk = SimulatedClock(base=base)
        assert clk.now() == base

    def test_simulated_clock_starts_at_default_base(self):
        """Clock without explicit base uses DEFAULT_BASE."""
        clk = SimulatedClock()
        assert clk.now() == SimulatedClock.DEFAULT_BASE

    def test_simulated_clock_advance_days(self):
        """advance(days=1) moves clock forward by exactly one day."""
        base = datetime(2026, 1, 15, 8, 0, 0)
        clk = SimulatedClock(base=base)
        result = clk.advance(days=1)
        expected = datetime(2026, 1, 16, 8, 0, 0)
        assert result == expected
        assert clk.now() == expected

    def test_simulated_clock_advance_hours(self):
        """advance(hours=3) moves clock forward by exactly 3 hours."""
        base = datetime(2026, 1, 15, 8, 0, 0)
        clk = SimulatedClock(base=base)
        result = clk.advance(hours=3)
        expected = datetime(2026, 1, 15, 11, 0, 0)
        assert result == expected

    def test_simulated_clock_multiple_advances_accumulate(self):
        """Multiple advance() calls accumulate correctly."""
        base = datetime(2026, 1, 15, 8, 0, 0)
        clk = SimulatedClock(base=base)
        clk.advance(days=1)
        clk.advance(hours=4)
        clk.advance(minutes=30)
        expected = datetime(2026, 1, 16, 12, 30, 0)
        assert clk.now() == expected

    def test_simulated_clock_reset(self):
        """reset() returns clock to base time."""
        base = datetime(2026, 1, 15, 8, 0, 0)
        clk = SimulatedClock(base=base)
        clk.advance(days=10)
        clk.reset()
        assert clk.now() == SimulatedClock.DEFAULT_BASE

    def test_simulated_clock_advance_returns_new_time(self):
        """advance() return value equals clk.now() after advance."""
        clk = SimulatedClock()
        returned = clk.advance(days=2, hours=6)
        assert returned == clk.now()


class TestRealClock:
    def test_real_clock_now_is_datetime(self):
        """RealClock.now() returns a datetime instance."""
        clk = RealClock()
        assert isinstance(clk.now(), datetime)

    def test_real_clock_advance_raises(self):
        """RealClock.advance() raises NotImplementedError."""
        clk = RealClock()
        with pytest.raises(NotImplementedError):
            clk.advance(days=1)
