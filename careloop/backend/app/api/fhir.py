"""FHIR Export router — read-only export conforming to HL7 FHIR R4 schema."""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import Appointment, Case, Consent, Message
from app.db.session import get_db
from app.fhir.mapping import (
    map_appointment_to_fhir,
    map_case_to_service_request,
    map_case_to_task,
    map_consent_to_fhir,
    map_message_to_communication,
)

router = APIRouter(prefix="/fhir", tags=["fhir"])


@router.get("/{resource_type}")
def get_fhir_bundle(
    resource_type: str,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Return a FHIR searchset bundle for the requested resource type."""
    resources: List[Dict[str, Any]] = []

    res = resource_type.lower()
    if res == "servicerequest":
        cases = db.query(Case).limit(limit).all()
        resources = [map_case_to_service_request(c) for c in cases]
    elif res == "task":
        cases = db.query(Case).limit(limit).all()
        resources = [map_case_to_task(c) for c in cases]
    elif res == "appointment":
        apts = db.query(Appointment).limit(limit).all()
        resources = [map_appointment_to_fhir(a) for a in apts]
    elif res == "communication":
        msgs = db.query(Message).limit(limit).all()
        resources = [map_message_to_communication(m) for m in msgs]
    elif res == "consent":
        consents = db.query(Consent).limit(limit).all()
        resources = [map_consent_to_fhir(c) for c in consents]
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Resource type '{resource_type}' not supported for export. Supported: ServiceRequest, Task, Appointment, Communication, Consent",
        )

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(resources),
        "entry": [{"resource": r} for r in resources],
    }
