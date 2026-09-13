from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(500))


class Genre(Base):
    __tablename__ = "genres"

    name: Mapped[str] = mapped_column(String(50), primary_key=True)


class MovieGenre(Base):
    __tablename__ = "movie_genres"

    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), primary_key=True)
    genre: Mapped[str] = mapped_column(ForeignKey("genres.name"), primary_key=True)


class DatasetRating(Base):
    """Public pseudonymous MovieLens identities, never application accounts."""

    __tablename__ = "dataset_ratings"
    __table_args__ = (
        CheckConstraint("rating >= 0.5 AND rating <= 5 AND rating * 2 = floor(rating * 2)"),
        Index("ix_dataset_ratings_movie_id", "movie_id"),
    )

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), primary_key=True)
    rating: Mapped[float]
    rated_at: Mapped[int] = mapped_column()


class DatasetImport(Base):
    __tablename__ = "dataset_imports"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(1000))
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    movie_count: Mapped[int]
    rating_count: Mapped[int]
    user_count: Mapped[int]
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DemoSession(Base):
    __tablename__ = "demo_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    state: Mapped[dict] = mapped_column(JSON)
