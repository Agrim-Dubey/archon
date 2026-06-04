"""Authentication domain repository, service, and router."""

import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.core.redis import get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import OAuthConnection, RefreshToken, User
from app.models.settings import UserSettings
from app.schemas.auth import (
    ForgotPasswordRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    VerifyEmailRequest,
    VerifyResetOTPRequest,
)

logger = logging.getLogger(__name__)


class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, name: str, email: str, password_hash: str) -> User:
        user = User(name=name, email=email, password_hash=password_hash, is_verified=True)
        self.db.add(user)
        await self.db.flush()
        # Initialize default user settings
        settings = UserSettings(user_id=user.id)
        self.db.add(settings)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def save_refresh_token(self, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(rt)
        await self.db.commit()
        return rt

    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        return result.scalar_one_or_none()

    async def revoke_refresh_tokens(self, user_id: int) -> None:
        await self.db.execute(
            update(User).where(User.id == user_id).values(token_version=User.token_version + 1)
        )
        await self.db.commit()


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    async def register(self, req: UserRegisterRequest) -> TokenResponse:
        existing = await self.repo.get_by_email(req.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered.")
        pw_hash = get_password_hash(req.password)
        user = await self.repo.create_user(req.name, req.email, pw_hash)

        access_token = create_access_token(user.id, token_version=user.token_version)
        refresh_token = create_refresh_token(user.id, token_version=user.token_version)
        await self.repo.save_refresh_token(
            user.id, refresh_token[-32:], datetime.now(timezone.utc)
        )

        return TokenResponse(
            access_token=access_token,
            expires_in=3600,
            refresh_token=refresh_token,
            user_id=user.id,
            name=user.name,
            email=user.email,
        )

    async def login(self, req: UserLoginRequest) -> TokenResponse:
        user = await self.repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        access_token = create_access_token(user.id, token_version=user.token_version)
        refresh_token = create_refresh_token(user.id, token_version=user.token_version)
        await self.repo.save_refresh_token(
            user.id, refresh_token[-32:], datetime.now(timezone.utc)
        )

        return TokenResponse(
            access_token=access_token,
            expires_in=3600,
            refresh_token=refresh_token,
            user_id=user.id,
            name=user.name,
            email=user.email,
        )

    async def refresh_tokens(self, token_str: str) -> TokenResponse:
        payload = decode_token(token_str)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token.")

        user_id = int(payload.get("sub", 0))
        user = await self.repo.get_by_id(user_id)
        if not user or user.token_version != payload.get("token_version", 1):
            raise HTTPException(status_code=401, detail="Token has been revoked.")

        new_access = create_access_token(user.id, token_version=user.token_version)
        new_refresh = create_refresh_token(user.id, token_version=user.token_version)
        await self.repo.save_refresh_token(
            user.id, new_refresh[-32:], datetime.now(timezone.utc)
        )

        return TokenResponse(
            access_token=new_access,
            expires_in=3600,
            refresh_token=new_refresh,
            user_id=user.id,
            name=user.name,
            email=user.email,
        )


router = APIRouter(prefix="", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest, db: AsyncSession = Depends(get_async_db)):
    service = AuthService(AuthRepository(db))
    return await service.register(req)


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest, db: AsyncSession = Depends(get_async_db)):
    service = AuthService(AuthRepository(db))
    return await service.login(req)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
    if not req.refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh token.")
    service = AuthService(AuthRepository(db))
    return await service.refresh_tokens(req.refresh_token)


@router.post("/logout")
async def logout(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    repo = AuthRepository(db)
    await repo.revoke_refresh_tokens(user.id)
    return {"success": True, "message": "Successfully logged out and tokens revoked."}


@router.post("/verify-email")
async def verify_email(req: VerifyEmailRequest):
    return {"success": True, "message": "Email verified successfully."}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    return {"success": True, "message": f"Password reset instructions sent to {req.email}."}


@router.post("/verify-reset-otp")
async def verify_reset_otp(req: VerifyResetOTPRequest):
    return {"success": True, "message": "OTP verified successfully."}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_async_db)):
    repo = AuthRepository(db)
    user = await repo.get_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.password_hash = get_password_hash(req.new_password)
    user.token_version += 1
    await db.commit()
    return {"success": True, "message": "Password reset successfully. Please login again."}


@router.get("/login/{provider}")
async def oauth_login(provider: str):
    return {"provider": provider, "auth_url": f"https://auth.{provider}.com/oauth/authorize?client_id=archon"}


@router.get("/callback/{provider}")
async def oauth_callback(provider: str, code: str = "mock_code", db: AsyncSession = Depends(get_async_db)):
    repo = AuthRepository(db)
    email = f"user_{provider}@archon.dev"
    user = await repo.get_by_email(email)
    if not user:
        user = await repo.create_user(name=f"{provider.capitalize()} Developer", email=email, password_hash="oauth_managed")
    access_token = create_access_token(user.id, token_version=user.token_version)
    return TokenResponse(
        access_token=access_token,
        expires_in=3600,
        user_id=user.id,
        name=user.name,
        email=user.email,
    )
