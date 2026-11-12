"""SQLAlchemy 2.x ORM models for CareLoop."""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return uuid4().hex


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class ProviderType(str, enum.Enum):
    lab = "lab"
    screening_program = "screening_program"
    primary_care = "primary_care"
    specialist = "specialist"
    hospital = "hospital"


class UserRole(str, enum.Enum):
    patient = "patient"
    navigator = "navigator"
    clinician = "clinician"
    supervisor = "supervisor"
    auditor = "auditor"
    admin = "admin"


class ReferralStatus(str, enum.Enum):
    sent = "sent"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


class AppointmentStatus(str, enum.Enum):
    offered = "offered"
    booked = "booked"
    attended = "attended"
    no_show = "no_show"
    cancelled = "cancelled"


class MessageStatus(str, enum.Enum):
    drafted = "drafted"
    validated = "validated"
    queued = "queued"
    delivered = "delivered"
    failed = "failed"
    acknowledged = "acknowledged"


class ClosureProposalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class SLAStatus(str, enum.Enum):
    running = "running"
    warned = "warned"
    breached = "breached"
    met = "met"


class AIActionKind(str, enum.Enum):
    message_rewrite = "message_rewrite"
    consult_summary = "consult_summary"
    closure_proposal_assist = "closure_proposal_assist"
    delay_reason_classify = "delay_reason_classify"


class AuditAction(str, enum.Enum):
    read = "read"
    write = "write"
    export = "export"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[ProviderType] = mapped_column(Enum(ProviderType), nullable=False)
    capacity_per_day: Mapped[int] = mapped_column(Integer, default=0)

    users: Mapped[List["User"]] = relationship("User", back_populates="provider")
    patients: Mapped[List["Patient"]] = relationship("Patient", back_populates="provider")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    synthetic_name: Mapped[str] = mapped_column(String, nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    sex: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, default="en")
    nationality_group: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone_stub: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    preferred_channel: Mapped[str] = mapped_column(String, default="app")
    care_setting: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    provider_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("providers.id"), nullable=True
    )

    provider: Mapped[Optional["Provider"]] = relationship("Provider", back_populates="patients")
    consents: Mapped[List["Consent"]] = relationship("Consent", back_populates="patient")
    cases: Mapped[List["Case"]] = relationship("Case", back_populates="patient")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="patient")


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    purpose: Mapped[str] = mapped_column(String, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="consents")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    provider_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("providers.id"), nullable=True
    )

    provider: Mapped[Optional["Provider"]] = relationship("Provider", back_populates="users")


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), nullable=False)
    pathway_id: Mapped[str] = mapped_column(String, nullable=False)
    urgency_tier: Mapped[str] = mapped_column(String, default="routine_actionable")
    current_state: Mapped[str] = mapped_column(String, nullable=False)
    owner_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id"), nullable=True
    )
    owner_provider_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("providers.id"), nullable=True
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closure_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="cases")
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])
    events: Mapped[List["CaseEvent"]] = relationship(
        "CaseEvent", back_populates="case", order_by="CaseEvent.seq"
    )
    referrals: Mapped[List["Referral"]] = relationship("Referral", back_populates="case")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="case")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="case")
    evidences: Mapped[List["Evidence"]] = relationship("Evidence", back_populates="case")
    closure_proposals: Mapped[List["ClosureProposal"]] = relationship(
        "ClosureProposal", back_populates="case"
    )
    sla_timers: Mapped[List["SLATimer"]] = relationship("SLATimer", back_populates="case")
    escalations: Mapped[List["Escalation"]] = relationship("Escalation", back_populates="case")


class CaseEvent(Base):
    """Append-only event ledger for a case."""

    __tablename__ = "case_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    from_state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    to_state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    actor_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    actor_role: Mapped[str] = mapped_column(String, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prev_hash: Mapped[str] = mapped_column(String, nullable=False)
    hash: Mapped[str] = mapped_column(String, nullable=False)

    case: Mapped["Case"] = relationship("Case", back_populates="events")
    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False)
    from_provider_id: Mapped[str] = mapped_column(
        String, ForeignKey("providers.id"), nullable=False
    )
    to_provider_id: Mapped[str] = mapped_column(
        String, ForeignKey("providers.id"), nullable=False
    )
    status: Mapped[ReferralStatus] = mapped_column(Enum(ReferralStatus), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="referrals")
    from_provider: Mapped["Provider"] = relationship("Provider", foreign_keys=[from_provider_id])
    to_provider: Mapped["Provider"] = relationship("Provider", foreign_keys=[to_provider_id])


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False)
    provider_id: Mapped[str] = mapped_column(String, ForeignKey("providers.id"), nullable=False)
    slot_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), nullable=False)

    case: Mapped["Case"] = relationship("Case", back_populates="appointments")
    provider: Mapped["Provider"] = relationship("Provider")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, nullable=False)
    template_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[MessageStatus] = mapped_column(Enum(MessageStatus), nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    validator_result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_action_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("ai_actions.id"), nullable=True
    )

    case: Mapped["Case"] = relationship("Case", back_populates="messages")
    patient: Mapped["Patient"] = relationship("Patient", back_populates="messages")
    ai_action: Mapped[Optional["AIAction"]] = relationship("AIAction")


class Evidence(Base):
    __tablename__ = "evidences"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String, nullable=False)
    ref: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    recorded_by: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="evidences")
    recorder: Mapped["User"] = relationship("User", foreign_keys=[recorded_by])


class ClosureProposal(Base):
    __tablename__ = "closure_proposals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False)
    proposed_by: Mapped[str] = mapped_column(String, nullable=False)
    basis_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ClosureProposalStatus] = mapped_column(
        Enum(ClosureProposalStatus), nullable=False
    )
    decided_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id"), nullable=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="closure_proposals")
    decider: Mapped[Optional["User"]] = relationship("User", foreign_keys=[decided_by])


class SLATimer(Base):
    __tablename__ = "sla_timers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False)
    step: Mapped[str] = mapped_column(String, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    warn_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[SLAStatus] = mapped_column(Enum(SLAStatus), nullable=False)

    case: Mapped["Case"] = relationship("Case", back_populates="sla_timers")


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False)
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    raised_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id"), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="escalations")
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to])


class AIAction(Base):
    __tablename__ = "ai_actions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    kind: Mapped[AIActionKind] = mapped_column(Enum(AIActionKind), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    input_hash: Mapped[str] = mapped_column(String, nullable=False)
    output_text: Mapped[str] = mapped_column(Text, nullable=False)
    validator_passed: Mapped[bool] = mapped_column(default=False)
    fallback_used: Mapped[bool] = mapped_column(default=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    actor_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)
    object_type: Mapped[str] = mapped_column(String, nullable=False)
    object_id: Mapped[str] = mapped_column(String, nullable=False)
    at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)

    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])


class SimRun(Base):
    __tablename__ = "sim_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)

    results: Mapped[List["SimResult"]] = relationship("SimResult", back_populates="run")


class SimResult(Base):
    __tablename__ = "sim_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String, ForeignKey("sim_runs.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    arm: Mapped[str] = mapped_column(String, nullable=False)
    group_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    group_value: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    ci_lower: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ci_upper: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    run: Mapped["SimRun"] = relationship("SimRun", back_populates="results")
