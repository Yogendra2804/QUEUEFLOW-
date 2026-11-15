"""
Auth endpoints: register and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_manager
from app.models.models import Manager
from app.schemas import LoginRequest, ManagerCreate, ManagerOut, Token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=ManagerOut, status_code=201)
def register(payload: ManagerCreate, db: Session = Depends(get_db)):
    existing = db.query(Manager).filter(Manager.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    manager = Manager(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(manager)
    db.commit()
    db.refresh(manager)
    return manager


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    manager = db.query(Manager).filter(Manager.email == payload.email).first()
    if not manager or not verify_password(payload.password, manager.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not manager.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    token = create_access_token(data={"sub": str(manager.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=ManagerOut)
def get_me(current_manager: Manager = Depends(get_current_manager)):
    return current_manager
