from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import RewardRedemptionOut, RewardItem
from app.services.auth import get_current_user, list_rewards, redeem_reward

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def _user_from_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
):
    if not credentials:
        return None
    return await get_current_user(session, credentials.credentials)


@router.get("/rewards")
async def rewards_catalog():
    return {"rewards": await list_rewards(None)}  # auth not required to view catalog


@router.post("/rewards/redeem")
async def redeem(
    reward_id: str,
    session: AsyncSession = Depends(get_db),
    user=Depends(_user_from_token),
):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        redemption = await redeem_reward(session, user, reward_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return redemption
