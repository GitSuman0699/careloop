# CareLoop

**Care-navigation tracking and simulation platform**

> [!CAUTION]
> **⚠️ ALL DATA IN THIS SYSTEM IS SYNTHETIC / SIMULATED.**
> **THIS SOFTWARE IS NOT FOR CLINICAL USE.**
> It is a demonstration and research tool only. No real patient data is stored, processed, or displayed.

## Overview

CareLoop is a full-stack application for modelling and simulating care-navigation pathways — the structured steps a patient follows from an initial screening result through to treatment or closure. It is designed to help health systems understand where patients are lost to follow-up ("leakage") and to test interventions that reduce it.

### Supported Pathways

| Pathway | Config |
|---|---|
| FIT Positive → Colonoscopy | `config/pathways/fit_positive_to_colonoscopy.json` |
| Breast Screening Recall | `config/pathways/breast_recall.json` |
| Cardiometabolic HbA1c Follow-up | `config/pathways/cardiometabolic_hba1c.json` |

## Quickstart

### Prerequisites

- Python ≥ 3.11
- Node.js ≥ 20
- Make (optional, for convenience targets)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npx vite dev
```

### Using Make

```bash
make dev       # Start backend + frontend dev servers
make test      # Run backend tests
make seed      # Generate synthetic seed data
make simulate  # Run simulation
make lint      # Lint backend code
make build     # Build frontend for production
```

### Docker

```bash
docker compose up --build
```

The application will be available at `http://localhost:8000`.

## Configuration

- **`config/assumptions.yaml`** — All tuneable parameters (currently PLACEHOLDER values)
- **`config/pathways/`** — Pathway step definitions, SLAs, urgency tiers
- **`config/templates/`** — Message templates (English + Arabic), banned terms

## Project Structure

```
careloop/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # Settings, security, clock
│   │   ├── domain/       # Domain models & business logic
│   │   ├── services/     # Application services
│   │   ├── ai/           # AI/ML integration layer
│   │   ├── adapters/     # External system adapters
│   │   ├── fhir/         # FHIR resource mappings
│   │   ├── db/           # Database models & sessions
│   │   └── seed/         # Synthetic data generators
│   ├── sim/              # Discrete-event simulation engine
│   └── tests/            # Backend test suite
├── frontend/
│   └── src/              # React + TypeScript UI
├── config/               # Assumptions, pathways, templates
├── docs/                 # Project documentation
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

## License

See [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) for dependency licenses.
