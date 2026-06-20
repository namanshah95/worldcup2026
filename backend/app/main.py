from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, attendance, auth, bingo, captain, games, pick_em, scores, trivia
from app.services.sports_sync import run_sync_loop

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    sync_task = None
    if settings.sportmonks_enabled:
        sync_task = asyncio.create_task(run_sync_loop())
        logger.info("Sportmonks auto-sync enabled")
    else:
        logger.info("Sportmonks auto-sync disabled (set SPORTS_API_KEY to enable)")
    yield
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="World Cup Watch Party API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(games.router, prefix="/api")
app.include_router(pick_em.router, prefix="/api")
app.include_router(captain.router, prefix="/api")
app.include_router(bingo.router, prefix="/api")
app.include_router(trivia.router, prefix="/api")
app.include_router(scores.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "sportmonks_sync": settings.sportmonks_enabled,
    }
