"""
FastAPI dependencies — current-manager extraction from JWT.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth import decode_token
from app.database import get_db
from app.models.models import Manager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_manager(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Manager:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    manager_id: int | None = payload.get("sub")
    if manager_id is None:
        raise credentials_exception
    manager = db.get(Manager, int(manager_id))
    if manager is None or not manager.is_active:
        raise credentials_exception
    return manager
