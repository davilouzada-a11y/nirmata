"""Shared FastAPI dependencies: auth and role checks."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter_by(id=payload["sub"]).first()
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user")
    return user


def require_reviewer(user: User = Depends(get_current_user)) -> User:
    """Only radiologists/admins may finalize a study via review."""
    if user.role not in {"radiologist", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only a radiologist can review studies")
    return user


def require_governance_admin(user: User = Depends(get_current_user)) -> User:
    """Only governance roles may change clinical policies."""
    if user.role not in {"admin", "admin_clinical"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only a clinical admin can manage policies")
    return user
