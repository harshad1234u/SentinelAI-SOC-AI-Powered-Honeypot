from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import TokenResponse, UserResponse
from app.middleware.auth import get_current_user, User
from app.core.security import create_access_token, verify_password
from app.core.config import get_settings
import os

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    settings = get_settings()
    admin_user = settings.ADMIN_USERNAME.strip()
    admin_pass = settings.ADMIN_PASSWORD.strip() # In production use hashed pass from env/db
    
    # Very simple static check for MVP
    if form_data.username == admin_user and form_data.password == admin_pass:
        token = create_access_token(data={"sub": admin_user, "role": "admin"})
        return {"access_token": token, "token_type": "bearer", "expires_in": 1800}
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    token = create_access_token(data={"sub": current_user.username, "role": current_user.role})
    return {"access_token": token, "token_type": "bearer", "expires_in": 1800}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
