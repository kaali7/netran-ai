"""
Netran AI — Authentication & Authorization Router.
Provides /signup, /login, and /me user endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.db import get_db
from api.models import User
from api.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserProfileUpdate,
    PasswordChangeRequest,
    MessageResponse,
    TokenResponse,
)
from api.security import hash_password, verify_password, create_access_token
from api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & Authorization"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new candidate or admin account."""
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    new_user = User(
        email=user_in.email.lower(),
        display_name=user_in.display_name.strip() if user_in.display_name else None,
        hashed_password=hash_password(user_in.password),
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user credentials and issue a signed JWT access token."""
    user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@router.post("/token", response_model=TokenResponse, summary="OAuth2 Token Login (Swagger Authorize)")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 password form login endpoint compatibility for Swagger UI Authorize button."""
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Fetch current authenticated user profile."""
    return current_user


@router.patch("/profile", response_model=UserResponse, summary="Update Candidate Profile")
def update_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile information such as display name."""
    if profile_in.display_name is not None:
        cleaned_name = profile_in.display_name.strip()
        current_user.display_name = cleaned_name if cleaned_name else None

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password", response_model=MessageResponse, summary="Change User Password")
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify current password and update to new password."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long."
        )

    current_user.hashed_password = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()
    return MessageResponse(message="Password updated successfully.")
