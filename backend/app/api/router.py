from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.seed import seed_if_empty
from app.core.database import SessionLocal, Base, make_engine
from fastapi.routing import APIRouter

from app.api import species, marine, predictions, observations, map_layers, users, rewards, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    try:
        engine = make_engine()
        async with engine.begin() as conn:
            # Ensure tables exist (idempotent) - uses sync DDL via run_sync
            await conn.run_sync(Base.metadata.create_all)
        async with SessionLocal() as session:
            await seed_if_empty(session)
        await engine.dispose()
    except Exception as exc:
        # Don't crash the app in dev if DB isn't reachable.
        print(f"[AquaTrack] DB init skipped due to: {exc}")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    # v1 API — use an APIRouter mounted on the app with /api prefix
    api_router = APIRouter(prefix="/api")
    api_router.include_router(species.router)
    api_router.include_router(marine.router)
    api_router.include_router(predictions.router)
    api_router.include_router(observations.router)
    api_router.include_router(map_layers.router)
    api_router.include_router(users.router)
    api_router.include_router(rewards.router)
    api_router.include_router(admin.router)
    app.include_router(api_router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": settings.app_name}

    return app
