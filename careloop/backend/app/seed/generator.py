"""Database seeder — seeds providers, users, ~5,000 synthetic patients, ~300 live cases, and demo scenarios A to F."""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta

from app.core.clock import get_clock
from app.core.ids import generate_id
from app.db.models import (
    Case,
    Consent,
    Patient,
    Provider,
    ProviderType,
    SLATimer,
    SLAStatus,
    User,
    UserRole,
)
from app.db.session import SessionLocal, init_db
from app.seed.scenarios import seed_demo_scenarios


def seed_all(num_patients: int = 5000, num_live_cases: int = 300):
    """Seed the database completely."""
    print("Initializing database tables...")
    init_db()
    db = SessionLocal()
    clock = get_clock()
    now = clock.now()

    print("Seeding healthcare providers...")
    p_screen = Provider(
        id="prov-screening-center",
        name="Abu Dhabi Community Screening Centre",
        type=ProviderType.screening_program,
        capacity_per_day=150,
    )
    p_primary = Provider(
        id="prov-primary-clinic",
        name="Al Bateen Primary Healthcare Clinic",
        type=ProviderType.primary_care,
        capacity_per_day=80,
    )
    p_special = Provider(
        id="prov-specialist-endo",
        name="Sheikh Shakhbout Endoscopy Specialist Pavilion",
        type=ProviderType.specialist,
        capacity_per_day=45,
    )
    p_lab = Provider(
        id="prov-central-lab",
        name="National Reference Pathology Lab",
        type=ProviderType.lab,
        capacity_per_day=1000,
    )
    db.add_all([p_screen, p_primary, p_special, p_lab])
    db.flush()

    providers_map = {
        "screening": p_screen,
        "primary": p_primary,
        "specialist": p_special,
        "lab": p_lab,
    }

    print("Seeding role-based demo users...")
    u_nav = User(id="user-nav-1", name="Sarah Jenkins (Navigator)", role=UserRole.navigator, provider_id=p_screen.id)
    u_clin = User(id="user-clin-1", name="Dr. Tariq Al-Hashimi (Clinician)", role=UserRole.clinician, provider_id=p_special.id)
    u_sup = User(id="user-sup-1", name="Mona Al-Zaabi (Ops Supervisor)", role=UserRole.supervisor, provider_id=p_screen.id)
    u_aud = User(id="user-aud-1", name="David Chen (Compliance Auditor)", role=UserRole.auditor, provider_id=p_screen.id)
    u_adm = User(id="user-admin-1", name="System Administrator", role=UserRole.admin, provider_id=p_screen.id)
    u_pat = User(id="user-patient-1", name="Patient User Portal", role=UserRole.patient, provider_id=p_screen.id)

    db.add_all([u_nav, u_clin, u_sup, u_aud, u_adm, u_pat])
    db.flush()

    users_map = {
        "navigator": u_nav,
        "clinician": u_clin,
        "supervisor": u_sup,
        "auditor": u_aud,
        "admin": u_adm,
        "patient": u_pat,
    }

    print("Seeding canonical demo cases (A to F)...")
    seed_demo_scenarios(db, providers_map, users_map)

    print(f"Seeding {num_patients} synthetic patient records...")
    rng = random.Random(42)
    first_names_en = ["John", "Emma", "Michael", "Sophia", "James", "Olivia", "William", "Ava"]
    last_names_en = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
    first_names_ar = ["Ahmed", "Fatima", "Mohammed", "Maryam", "Zaid", "Noor", "Khaled", "Reem"]
    last_names_ar = ["Al-Maktoum", "Al-Nuaimi", "Al-Qasimi", "Al-Zaabi", "Al-Shamsi", "Al-Kaabi"]

    languages = ["en", "ar", "ur", "other"]
    lang_weights = [0.55, 0.30, 0.10, 0.05]
    nationality_groups = ["Group_A", "Group_B", "Group_C"]
    care_settings = ["urban_clinic", "regional_hospital", "primary_centre"]

    patients = []
    for i in range(num_patients):
        lang = rng.choices(languages, weights=lang_weights, k=1)[0]
        if lang == "ar":
            name = f"{rng.choice(first_names_ar)} {rng.choice(last_names_ar)}"
        else:
            name = f"{rng.choice(first_names_en)} {rng.choice(last_names_en)}"

        y = rng.randint(1950, 1980)
        m = rng.randint(1, 12)
        d = rng.randint(1, 28)
        dob_val = date(y, m, d)
        sex_val = rng.choice(["F", "M"])

        pt = Patient(
            id=f"pt-synth-{i:05d}",
            synthetic_name=name,
            dob=dob_val,
            sex=sex_val,
            language=lang,
            nationality_group=rng.choice(nationality_groups),
            phone_stub=f"+971 50 *** {rng.randint(1000, 9999)}",
            preferred_channel=rng.choice(["app", "sms"]),
            care_setting=rng.choice(care_settings),
            provider_id=p_screen.id,
        )
        patients.append(pt)

    db.bulk_save_objects(patients)
    db.commit()

    print(f"Seeding {num_live_cases} active cases across pathway states...")
    states = [
        "RESULT_ISSUED", "PATIENT_NOTIFIED", "PATIENT_ACKNOWLEDGED",
        "CONFIRMATION_DONE", "REFERRAL_SENT", "REFERRAL_ACCEPTED",
        "APPOINTMENT_BOOKED", "APPOINTMENT_ATTENDED", "TREATMENT_OR_SURVEILLANCE",
        "CLOSURE_PROPOSED", "CLOSED",
    ]
    pathways = ["fit_positive_to_colonoscopy", "breast_recall", "cardiometabolic_hba1c"]

    live_cases = []
    timers = []
    for c_idx in range(num_live_cases):
        chosen_pt = patients[c_idx]
        chosen_state = rng.choice(states)
        chosen_pathway = rng.choices(pathways, weights=[0.70, 0.15, 0.15], k=1)[0]
        urgency = "urgent" if (c_idx % 15 == 0) else ("priority" if (c_idx % 6 == 0) else "routine_actionable")

        open_days_ago = rng.randint(1, 40)
        opened_dt = now - timedelta(days=open_days_ago)
        closed_dt = (opened_dt + timedelta(days=rng.randint(15, 30))) if chosen_state == "CLOSED" else None

        c = Case(
            id=f"case-live-{c_idx:04d}",
            patient_id=chosen_pt.id,
            pathway_id=chosen_pathway,
            urgency_tier=urgency,
            current_state=chosen_state,
            owner_id=u_nav.id if (c_idx % 8 != 0) else None,  # some unassigned
            owner_provider_id=p_screen.id,
            opened_at=opened_dt,
            closed_at=closed_dt,
            closure_type="completed_treatment" if closed_dt else None,
        )
        live_cases.append(c)

        # Attach SLA timer
        if not closed_dt:
            is_breached = (c_idx % 7 == 0)
            is_warned = (c_idx % 5 == 0 and not is_breached)
            due = now - timedelta(days=1) if is_breached else now + timedelta(days=5)
            warn = now - timedelta(days=2) if (is_warned or is_breached) else now + timedelta(days=2)
            timer_status = SLAStatus.breached if is_breached else (SLAStatus.warned if is_warned else SLAStatus.running)

            t = SLATimer(
                id=generate_id(),
                case_id=c.id,
                step=chosen_state,
                due_at=due,
                warn_at=warn,
                status=timer_status,
            )
            timers.append(t)

    db.bulk_save_objects(live_cases)
    db.bulk_save_objects(timers)
    db.commit()

    print("Seed complete! Created 4 providers, 6 users, 6 demo cases, 5000 patients, and 300 active cases.")


if __name__ == "__main__":
    seed_all()

