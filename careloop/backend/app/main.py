"""CareLoop backend — FastAPI application entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import audit, cases, clock, closure, fhir, messages, ops, pathways, patients, queues, sim
from app.api.auth import DemoLoginRequest, TokenResponse, create_token
from app.core.clock import SimulatedClock, get_clock
from app.core.ids import generate_id
from app.db.models import Provider, ProviderType, User, UserRole
from app.db.session import get_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize DB tables
    init_db()
    yield


app = FastAPI(
    title="CareLoop API",
    description="Care-navigation tracking with simulated data — NOT FOR CLINICAL USE",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    clk = get_clock()
    return {
        "status": "ok",
        "service": "careloop",
        "clock_mode": "simulated" if isinstance(clk, SimulatedClock) else "real",
        "current_time": clk.now().isoformat(),
        "disclaimer": "SIMULATED DATA: NOT FOR CLINICAL USE",
    }


@app.post("/api/auth/demo-login", response_model=TokenResponse, tags=["auth"])
def demo_login(req: DemoLoginRequest, db: Session = Depends(get_db)):
    """Demo login endpoint for quick role-switching in the UI and automated demos."""
    role_str = req.role.lower()

    # Find existing user with role or create one
    user = db.query(User).filter(User.role == role_str).first()
    if not user:
        # Ensure default provider exists
        provider = db.query(Provider).first()
        if not provider:
            provider = Provider(
                id=generate_id(),
                name="Central Health Screening Network",
                type=ProviderType.screening_program,
                capacity_per_day=100,
            )
            db.add(provider)
            db.flush()

        user = User(
            id=generate_id(),
            name=req.user_name or f"Demo {role_str.capitalize()}",
            role=role_str,
            provider_id=provider.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_token(user_id=user.id, user_name=user.name, role=role_str)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        user_name=user.name,
        role=role_str,
    )


# Include API routers
app.include_router(cases.router, prefix="/api")
app.include_router(closure.router, prefix="/api")
app.include_router(queues.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(ops.router, prefix="/api")
app.include_router(clock.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(fhir.router, prefix="/api")
app.include_router(sim.router, prefix="/api")
app.include_router(pathways.router, prefix="/api")

# Mount static frontend build if present
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
