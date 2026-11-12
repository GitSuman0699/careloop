"""Pytest fixtures for CareLoop test suite."""

from __future__ import annotations

import os
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure CLOCK_MODE is simulated for all tests and no DB file is used
os.environ.setdefault("CLOCK_MODE", "simulated")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.core.clock import SimulatedClock, _reset_clock
from app.db.models import Base, Case, Patient, Provider, ProviderType, User, UserRole
from app.domain.pathway_loader import load_pathway, PathwayConfig


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_session():
    """In-memory SQLite session; all tables created before and dropped after."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session: Session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


# ---------------------------------------------------------------------------
# Clock fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def clock():
    """SimulatedClock starting at 2026-01-15 08:00:00 UTC."""
    _reset_clock()
    return SimulatedClock(base=datetime(2026, 1, 15, 8, 0, 0))


# ---------------------------------------------------------------------------
# Config / pathway fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def fit_pathway() -> PathwayConfig:
    """Load the fit_positive_to_colonoscopy pathway config."""
    return load_pathway("fit_positive_to_colonoscopy")


# ---------------------------------------------------------------------------
# DB entity fixtures (depend on db_session)
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_provider(db_session: Session) -> Provider:
    """Create a Provider in the test DB."""
    provider = Provider(
        name="Test Screening Centre",
        type=ProviderType.screening_program,
        capacity_per_day=50,
    )
    db_session.add(provider)
    db_session.flush()
    return provider


@pytest.fixture()
def sample_user(db_session: Session, sample_provider: Provider) -> User:
    """Create a User with navigator role in the test DB."""
    user = User(
        name="Test Navigator",
        role=UserRole.navigator,
        provider_id=sample_provider.id,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def sample_patient(db_session: Session, sample_provider: Provider) -> Patient:
    """Create a Patient in the test DB."""
    patient = Patient(
        synthetic_name="Test Patient",
        dob=date(1960, 6, 15),
        sex="F",
        language="en",
        preferred_channel="app",
        provider_id=sample_provider.id,
    )
    db_session.add(patient)
    db_session.flush()
    return patient


@pytest.fixture()
def sample_case(db_session: Session, sample_patient: Patient) -> Case:
    """Create a Case in RESULT_ISSUED state in the test DB."""
    case = Case(
        patient_id=sample_patient.id,
        pathway_id="fit_positive_to_colonoscopy",
        urgency_tier="routine_actionable",
        current_state="RESULT_ISSUED",
        opened_at=datetime(2026, 1, 15, 8, 0, 0),
    )
    db_session.add(case)
    db_session.flush()
    return case
