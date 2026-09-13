import hashlib
import secrets
import time
import uuid
from collections import OrderedDict, deque
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DemoSession
from app.recommender import DEMO_RATINGS, load_catalog, rank

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]
limiter: OrderedDict[str, deque] = OrderedDict()
limiter_lock = Lock()


class Preferences(BaseModel):
    ratings: dict[str, float] = Field(default_factory=dict, max_length=2000)
    saved: list[int] = Field(default_factory=list, max_length=500)
    liked: list[int] = Field(default_factory=list, max_length=500)
    genres: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("ratings")
    @classmethod
    def valid_ratings(cls, value):
        for key, rating in value.items():
            if not key.isdecimal() or not 0.5 <= rating <= 5 or rating * 2 != int(rating * 2):
                raise ValueError(
                    "Ratings must use movie IDs and half-star increments from 0.5 to 5"
                )
        return value


def check_origin(request: Request):
    import os

    allowed = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    origin = request.headers.get("origin")
    if origin and origin not in allowed:
        raise HTTPException(403, "Origin is not allowed")


def current_session(request: Request, db: DB) -> DemoSession:
    token = request.cookies.get("signalrank_session", "")
    session = (
        db.scalar(
            select(DemoSession).where(
                DemoSession.token_hash == hashlib.sha256(token.encode()).hexdigest(),
                DemoSession.expires_at > datetime.now(UTC),
            )
        )
        if token
        else None
    )
    if session is None:
        raise HTTPException(401, "Start a demo session first")
    return session


@router.post("/auth/demo", tags=["Demo"], response_model=Preferences)
def demo(request: Request, response: Response, db: DB):
    check_origin(request)
    try:
        return current_session(request, db).state
    except HTTPException:
        pass
    # One process in the local stack. A public API deployment must move this to shared storage.
    address = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with limiter_lock:
        recent = limiter.setdefault(address, deque())
        while recent and recent[0] < now - 600:
            recent.popleft()
        if len(recent) >= 20:
            raise HTTPException(429, "Too many new demo sessions. Please try again later.")
        recent.append(now)
        limiter.move_to_end(address)
        while len(limiter) > 4096:
            limiter.popitem(last=False)
    db.execute(delete(DemoSession).where(DemoSession.expires_at <= datetime.now(UTC)))
    token = secrets.token_urlsafe(32)
    state = Preferences(ratings=DEMO_RATINGS, genres=["Sci-Fi", "Adventure"]).model_dump()
    db.add(
        DemoSession(
            id=str(uuid.uuid4()),
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(days=7),
            state=state,
        )
    )
    db.commit()
    response.set_cookie(
        "signalrank_session",
        token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=7 * 86400,
    )
    return state


@router.get("/me", tags=["Demo"], response_model=Preferences)
def me(session: Annotated[DemoSession, Depends(current_session)]):
    return session.state


@router.put("/me", tags=["Demo"], response_model=Preferences)
def update_me(
    preferences: Preferences,
    request: Request,
    db: DB,
    session: Annotated[DemoSession, Depends(current_session)],
):
    check_origin(request)
    catalog = load_catalog()
    ids = {m["id"] for m in catalog["movies"]}
    genres = {g for m in catalog["movies"] for g in m["genres"]}
    submitted = set(map(int, preferences.ratings)) | set(preferences.saved) | set(preferences.liked)
    if not submitted <= ids or not set(preferences.genres) <= genres:
        raise HTTPException(422, "Unknown movie or genre")
    session.state = preferences.model_dump()
    db.commit()
    return session.state


@router.delete("/auth/session", tags=["Demo"], status_code=204)
def logout(
    request: Request,
    response: Response,
    db: DB,
    session: Annotated[DemoSession, Depends(current_session)],
):
    check_origin(request)
    db.delete(session)
    db.commit()
    response.delete_cookie("signalrank_session")


@router.get("/catalog", tags=["Catalog"])
def catalog():
    return load_catalog()


@router.get("/movies", tags=["Catalog"])
def movies(
    q: str = Query("", max_length=200),
    genre: str = "",
    offset: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
):
    found = [
        m
        for m in load_catalog()["movies"]
        if q.casefold() in m["title"].casefold() and (not genre or genre in m["genres"])
    ]
    return {"total": len(found), "items": found[offset : offset + limit]}


@router.get("/recommendations", tags=["Recommendations"])
def recommendations(
    session: Annotated[DemoSession, Depends(current_session)], limit: int = Query(24, ge=1, le=100)
):
    return {"items": rank(load_catalog(), session.state, limit)}


@router.get("/analytics", tags=["Analytics"])
def analytics(session: Annotated[DemoSession, Depends(current_session)]):
    data = load_catalog()
    return {
        "movies": len(data["movies"]),
        "ratings": data["rating_count"],
        "dataset_users": data["user_count"],
        "evaluation": data["evaluation"],
        "your_ratings": len(session.state["ratings"]),
        "your_saves": len(session.state["saved"]),
    }
