from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse
from app.auth.service import AuthService
from app.users.schemas import UserRead
from app.shared.db.session import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя (POST /auth/register)."""
    service = AuthService(db)
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    """Вход в систему с получением JWT токена (POST /auth/login)."""
    service = AuthService(db)
    return await service.login(data)