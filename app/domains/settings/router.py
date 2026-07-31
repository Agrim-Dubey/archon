"""User profile settings domain."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.settings import UserSettings
from app.models.user import User
from app.schemas.settings import UserSettingsSchema, UserSettingsUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


@router.get("", response_model=UserSettingsSchema)
async def get_settings(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user.id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.put("", response_model=UserSettingsSchema)
async def update_settings(
    req: UserSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user.id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)

    update_data = req.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(settings, field, val)

    await db.commit()
    await db.refresh(settings)
    return settings
