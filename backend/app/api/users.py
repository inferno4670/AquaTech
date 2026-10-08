from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schemas import Credentials, LoginResponse, PointsSnapshot, UserCreate, UserPublic
from app.services.auth import authenticate_user, create_user, get_user_public, get_current_user, issue_token_for_user

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def _user_from_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
):
    if not credentials:
        return None
    user = await get_current_user(session, credentials.credentials)
    return user


@router.post("/auth/register", status_code=201)
async def register(body: UserCreate, session: AsyncSession = Depends(get_db)):
    existing = await authenticate_user(session, body.email, body.password)  # placeholder; implement lookup
    from app.models.models import User
    from sqlalchemy import select
    result = await session.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = await create_user(session, body.email, body.password, body.display_name)
    token = await issue_token_for_user(user)
    public = await get_user_public(session, user)
    return LoginResponse(user=public, token=token)


@router.post("/auth/login")
async def login(body: Credentials, session: AsyncSession = Depends(get_db)):
    user = await authenticate_user(session, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = await issue_token_for_user(user)
    public = await get_user_public(session, user)
    return LoginResponse(user=public, token=token)


@router.get("/users/me")
async def me(
    session: AsyncSession = Depends(get_db),
    user=Depends(_user_from_token),
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    # Real aggregates (level, reputation, observation counts) rather than zeros, so
    # the profile page and the admin nav entry reflect the actual account.
    return await get_user_public(session, user)


@router.get("/users/me/points", response_model=PointsSnapshot)
async def points(
    session: AsyncSession = Depends(get_db),
    user=Depends(_user_from_token),
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    from app.services.auth import get_points_snapshot
    return await get_points_snapshot(session, user)
