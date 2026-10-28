"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from app.db.base import get_db
from app.db.models.user import User
from .models import Token
from .utils import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["auth"])

# ═══════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None

# ═══════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════
@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    # بررسی وجود کاربر
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # ساخت کاربر جدید
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        display_name=user_data.display_name or user_data.email.split("@")[0],
        hashed_password=hashed_password  # ⚠️ باید به مدل User اضافه شود
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # ساخت توکن
    access_token = create_access_token(data={"sub": new_user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # پیدا کردن کاربر با ایمیل
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ساخت توکن
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}