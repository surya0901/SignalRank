"""Download and transactionally import MovieLens. Never extract untrusted ZIP paths."""

import csv
import hashlib
import io
import json
import logging
import math
import os
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import func, insert, select, text
from sqlalchemy.orm import Session

from app.config import MOVIELENS_MIRROR, MOVIELENS_SHA256, MOVIELENS_URL, get_settings
from app.db import get_engine
from app.models import DatasetImport, DatasetRating, Genre, Movie, MovieGenre

logger = logging.getLogger(__name__)
MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_MEMBER_BYTES = 40 * 1024 * 1024
PREFIX = "ml-latest-small/"


def read_csv(archive: zipfile.ZipFile, name: str):
    member = archive.getinfo(PREFIX + name)
    if member.file_size > MAX_MEMBER_BYTES:
        raise ValueError(f"Dataset member too large: {name}")
    with archive.open(member) as raw:
        yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig"))


def parse_archive(path: Path):
    movies, movie_genres, ratings = [], [], []
    genres, seen_movies, seen_ratings = set(), set(), set()
    with zipfile.ZipFile(path) as archive:
        for row in read_csv(archive, "movies.csv"):
            movie_id = int(row["movieId"])
            if movie_id <= 0 or movie_id in seen_movies or not row["title"].strip():
                raise ValueError("Invalid or duplicate movie")
            seen_movies.add(movie_id)
            movies.append({"id": movie_id, "title": row["title"]})
            for genre in sorted(set(row["genres"].split("|")) - {"(no genres listed)", ""}):
                genres.add(genre)
                movie_genres.append({"movie_id": movie_id, "genre": genre})
        for row in read_csv(archive, "ratings.csv"):
            user_id, movie_id = int(row["userId"]), int(row["movieId"])
            rating, timestamp = float(row["rating"]), int(row["timestamp"])
            key = (user_id, movie_id)
            if (
                user_id <= 0
                or movie_id not in seen_movies
                or key in seen_ratings
                or not math.isfinite(rating)
                or not 0.5 <= rating <= 5
                or rating * 2 != int(rating * 2)
                or timestamp < 0
            ):
                raise ValueError("Invalid or duplicate rating")
            seen_ratings.add(key)
            ratings.append(
                {
                    "user_id": user_id,
                    "movie_id": movie_id,
                    "rating": rating,
                    "rated_at": timestamp,
                }
            )
    if not movies or not ratings:
        raise ValueError("Dataset is empty")
    return movies, [{"name": name} for name in sorted(genres)], movie_genres, ratings


def download_archive(target: Path, url: str, expected_sha256: str) -> str:
    if urlparse(url).scheme != "https":
        raise ValueError("DATASET_URL must use HTTPS")
    if len(expected_sha256) != 64:
        raise ValueError("A trusted SHA-256 is required before downloading")
    temporary = target.with_suffix(".partial")
    sources = [url]
    if url == MOVIELENS_URL and expected_sha256.lower() == MOVIELENS_SHA256:
        sources.append(MOVIELENS_MIRROR)
    try:
        for index, candidate in enumerate(sources):
            try:
                with urllib.request.urlopen(candidate, timeout=30) as response:
                    actual_source = response.geturl()
                    if urlparse(actual_source).scheme != "https":
                        raise ValueError("Dataset download redirected away from HTTPS")
                    with temporary.open("wb") as out:
                        total = 0
                        checksum = hashlib.sha256()
                        while chunk := response.read(64 * 1024):
                            total += len(chunk)
                            if total > MAX_ARCHIVE_BYTES:
                                raise ValueError("Dataset archive exceeds size limit")
                            checksum.update(chunk)
                            out.write(chunk)
                if checksum.hexdigest() != expected_sha256.lower():
                    raise ValueError("Dataset SHA-256 does not match DATASET_SHA256")
                target.with_suffix(".source.json").write_text(
                    json.dumps(
                        {
                            "source": actual_source,
                            "sha256": checksum.hexdigest(),
                        }
                    )
                )
                os.replace(temporary, target)
                return actual_source
            except (urllib.error.URLError, TimeoutError):
                if index == len(sources) - 1:
                    raise
                logger.warning(
                    "Primary download unavailable; trying HTTPS mirror with pinned SHA-256"
                )
    finally:
        temporary.unlink(missing_ok=True)
    raise RuntimeError("No dataset source available")


def import_archive(db: Session, path: Path, source: str, expected_sha256: str = "") -> dict:
    """Caller owns the transaction. A changed dataset requires an explicit fresh database."""
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Dataset archive exceeds size limit")
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_sha256 and checksum != expected_sha256.lower():
        raise ValueError("Dataset SHA-256 does not match DATASET_SHA256")
    existing = db.scalar(select(DatasetImport).limit(1))
    if existing:
        if existing.sha256 != checksum:
            raise ValueError("Database contains a different dataset; refusing to mix versions")
        if (
            db.scalar(select(func.count()).select_from(Movie)) != existing.movie_count
            or db.scalar(select(func.count()).select_from(DatasetRating)) != existing.rating_count
        ):
            raise ValueError(
                "Imported dataset counts no longer match; investigate before restarting"
            )
        return {"status": "already_imported", "sha256": checksum}
    movies, genres, movie_genres, ratings = parse_archive(path)
    for model, records in [
        (Movie, movies),
        (Genre, genres),
        (MovieGenre, movie_genres),
        (DatasetRating, ratings),
    ]:
        for start in range(0, len(records), 2000):
            db.execute(insert(model), records[start : start + 2000])
    result = {
        "source": source,
        "sha256": checksum,
        "movie_count": len(movies),
        "rating_count": len(ratings),
        "user_count": len({r["user_id"] for r in ratings}),
    }
    db.add(DatasetImport(**result))
    return {"status": "imported", **result}


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    archive = settings.data_dir / "ml-latest-small.zip"
    with Session(get_engine()) as db, db.begin():
        # Serializes concurrent initializers and makes the import marker atomic with the rows.
        db.execute(text("SELECT pg_advisory_xact_lock(734819201)"))
        if not archive.exists():
            logger.info("Downloading MovieLens from %s", settings.dataset_url)
            download_archive(archive, settings.dataset_url, settings.dataset_sha256)
        source = "manual archive: ml-latest-small.zip"
        source_file = archive.with_suffix(".source.json")
        if source_file.exists():
            provenance = json.loads(source_file.read_text())
            if provenance["sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest():
                source = provenance["source"]
        result = import_archive(db, archive, source, settings.dataset_sha256)
        with zipfile.ZipFile(archive) as zipped:
            readme = zipped.getinfo(PREFIX + "README.txt")
            if readme.file_size > MAX_MEMBER_BYTES:
                raise ValueError("Dataset README exceeds size limit")
            (settings.data_dir / "MOVIELENS-README.txt").write_bytes(zipped.read(readme))
    logger.info("Dataset initialization: %s", json.dumps(result))


if __name__ == "__main__":
    main()
