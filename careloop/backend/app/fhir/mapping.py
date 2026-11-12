"""FHIR R4 Mapping layer — transforms internal CareLoop entities to read-only FHIR resources."""

from __future__ import annotations

from typing import Any, Dict, List
from app.db.models import Appointment, Case, Consent, Message


def map_case_to_service_request(case: Case) -> Dict[str, Any]:
    """Map internal Case to FHIR ServiceRequest."""
    return {
        "resourceType": "ServiceRequest",
        "id": case.id,
        "status": "completed" if case.closed_at else "active",
        "intent": "order",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "410606002",
                        "display": "Screening procedure",
                    }
                ]
            }
        ],
        "priority": "urgent" if case.urgency_tier == "urgent" else "routine",
        "subject": {"reference": f"Patient/{case.patient_id}"},
        "authoredOn": case.opened_at.isoformat() if case.opened_at else None,
        "requester": {"reference": f"Practitioner/{case.owner_id}"} if case.owner_id else None,
        "note": [{"text": f"CareLoop pathway: {case.pathway_id}, state: {case.current_state}"}],
    }


def map_case_to_task(case: Case) -> Dict[str, Any]:
    """Map internal Case to FHIR Task."""
    return {
        "resourceType": "Task",
        "id": f"task-{case.id}",
        "basedOn": [{"reference": f"ServiceRequest/{case.id}"}],
        "status": "completed" if case.closed_at else "in-progress",
        "businessStatus": {"text": case.current_state},
        "intent": "order",
        "priority": "urgent" if case.urgency_tier == "urgent" else "routine",
        "for": {"reference": f"Patient/{case.patient_id}"},
        "owner": {"reference": f"Practitioner/{case.owner_id}"} if case.owner_id else None,
        "authoredOn": case.opened_at.isoformat() if case.opened_at else None,
    }


def map_appointment_to_fhir(apt: Appointment) -> Dict[str, Any]:
    """Map internal Appointment to FHIR Appointment."""
    status_map = {
        "offered": "proposed",
        "booked": "booked",
        "attended": "fulfilled",
        "no_show": "noshow",
        "cancelled": "cancelled",
    }
    raw_status = apt.status.value if hasattr(apt.status, "value") else str(apt.status)
    return {
        "resourceType": "Appointment",
        "id": apt.id,
        "status": status_map.get(raw_status, "booked"),
        "start": apt.slot_at.isoformat() if apt.slot_at else None,
        "participant": [
            {
                "actor": {"reference": f"Location/{apt.provider_id}"},
                "status": "accepted",
            }
        ],
    }


def map_message_to_communication(msg: Message) -> Dict[str, Any]:
    """Map internal Message to FHIR Communication."""
    return {
        "resourceType": "Communication",
        "id": msg.id,
        "status": "completed" if msg.status.value == "delivered" else "in-progress",
        "subject": {"reference": f"Patient/{msg.patient_id}"},
        "sent": msg.sent_at.isoformat() if msg.sent_at else None,
        "payload": [{"contentString": msg.body}],
        "medium": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode",
                        "code": "SMSWRIT" if msg.channel == "sms" else "ELECTRONIC",
                    }
                ]
            }
        ],
    }


def map_consent_to_fhir(consent: Consent) -> Dict[str, Any]:
    """Map internal Consent to FHIR Consent."""
    return {
        "resourceType": "Consent",
        "id": consent.id,
        "status": "inactive" if consent.revoked_at else "active",
        "scope": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                    "code": "patient-privacy",
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "INFA",
                        "display": "information access",
                    }
                ]
            }
        ],
        "patient": {"reference": f"Patient/{consent.patient_id}"},
        "dateTime": consent.granted_at.isoformat() if consent.granted_at else None,
    }

