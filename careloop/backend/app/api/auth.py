"""Authentication and RBAC dependency injection with demo role switching."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.clock import get_clock
from app.core.ids import generate_id
from app.core.rbac import Role, check_permission
from app.db.models import AuditAction, AuditLog, User, UserRole
from app.db.session import get_db

SECRET_KEY = os.environ.get("JWT_SECRET", "careloop-prototype-secret-key-2026")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


class DemoLoginRequest(BaseModel):
    role: str = "navigator"
    user_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_name: str
    role: str


def create_token(user_id: str, user_name: str, role: str) -> str:
    clock = get_clock()
    now = clock.now()
    payload = {
        "sub": user_id,
        "name": user_name,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    x_demo_role: Optional[str] = Header(None, alias="X-Demo-Role"),
    x_demo_user_id: Optional[str] = Header(None, alias="X-Demo-User-Id"),
) -> User:
    """Extract authenticated user from JWT token, or use demo header if provided."""
    # 1. If explicit demo header is provided (for easy demo testing)
    if x_demo_role:
        role_val = x_demo_role.lower()
        user = db.query(User).filter(User.role == role_val).first()
        if not user:
            user = User(
                id=x_demo_user_id or generate_id(),
                name=f"Demo {role_val.capitalize()}",
                role=role_val,
            )
            db.add(user)
            db.flush()
        return user

    # 2. Extract from JWT
    if not creds:
        # Fallback to default demo navigator user
        user = db.query(User).filter(User.role == UserRole.navigator).first()
        if not user:
            user = User(
                id="demo-nav-1",
                name="Demo Navigator",
                role=UserRole.navigator,
            )
            db.add(user)
            db.flush()
        return user

    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, name=payload.get("name", "User"), role=role)
            db.add(user)
            db.flush()
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_permission(capability: str):
    """Dependency that enforces permission and logs the access in AuditLog."""
    def dependency(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        if not check_permission(user_role_str, capability):
            # Log denied attempt
            clock = get_clock()
            log = AuditLog(
                id=generate_id(),
                actor_id=user.id,
                role=user_role_str,
                action=AuditAction.read,
                object_type="permission_denied",
                object_id=capability,
                at=clock.now(),
                purpose=f"Access denied for capability: {capability}",
            )
            db.add(log)
            db.flush()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role_str}' does not have capability '{capability}'",
            )
        return user

    return dependency
