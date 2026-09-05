from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=TokenResponse
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    allowed_roles = {
        "CUSTOMER",
        "TECHNICIAN",
        "ADMIN"
    }

    role = request.role.upper()

    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )

    user = User(
        name=request.name,
        email=request.email,
        password=hash_password(request.password),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
        "email": user.email,
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(
        request.password,
        user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
        "email": user.email,
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }