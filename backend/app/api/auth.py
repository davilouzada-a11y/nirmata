from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import Token, UserOut, LoginRequest
from app.api.deps import get_current_user

router = APIRouter()


def _authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password")
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password flow. `username` carries the email (Swagger-friendly)."""
    user = _authenticate(db, form.username, form.password)
    token = create_access_token(subject=user.id, role=user.role)
    return Token(access_token=token)


@router.post("/login/json", response_model=Token)
def login_json(payload: LoginRequest, db: Session = Depends(get_db)):
    """JSON login for the frontend client."""
    user = _authenticate(db, payload.email, payload.password)
    return Token(access_token=create_access_token(subject=user.id, role=user.role))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
