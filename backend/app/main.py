from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import router
from app.db import get_db
from app.models import DatasetImport, DatasetRating, Genre, Movie

app = FastAPI(
    title="SignalRank API",
    description="Movie discovery with isolated demo profiles and explainable recommendations.",
    version="1.0.0",
)
app.include_router(router)
Database = Annotated[Session, Depends(get_db)]


@app.get("/health/live", tags=["Operations"])
def live():
    return {"status": "ok"}


@app.get("/health/ready", tags=["Operations"])
def ready(db: Database):
    try:
        db.execute(text("SELECT 1"))
        imported = db.scalar(select(DatasetImport.id).limit(1))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is not ready") from exc
    if imported is None:
        raise HTTPException(status_code=503, detail="Dataset import is not complete")
    return {"status": "ready"}


@app.get("/api/dataset", tags=["Dataset"])
def dataset(db: Database):
    imported = db.scalar(select(DatasetImport).order_by(DatasetImport.id.desc()).limit(1))
    if imported is None:
        raise HTTPException(status_code=503, detail="Dataset import is not complete")
    return {
        "name": "MovieLens latest-small",
        "movies": db.scalar(select(func.count()).select_from(Movie)),
        "ratings": db.scalar(select(func.count()).select_from(DatasetRating)),
        "users": db.scalar(select(func.count(func.distinct(DatasetRating.user_id)))),
        "genres": db.scalar(select(func.count()).select_from(Genre)),
        "sha256": imported.sha256,
        "source": imported.source,
        "imported_at": imported.imported_at,
    }
