"""Build the production catalog artifact and a separate leakage-controlled evaluation."""

import json
import logging
from collections import defaultdict
from datetime import UTC, datetime

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import DatasetImport, DatasetRating, Movie, MovieGenre
from app.recommender import build_catalog, rank


def evaluate(movies, ratings):
    cutoff = int(np.quantile([r["rated_at"] for r in ratings], 0.8))
    train = [r for r in ratings if r["rated_at"] <= cutoff]
    test = [r for r in ratings if r["rated_at"] > cutoff]
    seen_ids = {r["movie_id"] for r in train}
    model = build_catalog([m for m in movies if m["id"] in seen_ids], train)
    history, positives = defaultdict(dict), defaultdict(set)
    for r in train:
        history[r["user_id"]][str(r["movie_id"])] = r["rating"]
    for r in test:
        if r["rating"] >= 4 and r["movie_id"] in seen_ids:
            positives[r["user_id"]].add(r["movie_id"])
    eligible = sorted(u for u in positives if len(history[u]) >= 5)
    measured = {"hybrid": [], "popularity": []}
    coverage = {"hybrid": set(), "popularity": set()}
    popularity = sorted(model["movies"], key=lambda m: (-m["quality"], -m["count"], m["id"]))
    for user in eligible:
        recommendations = {
            "hybrid": rank(model, {"ratings": history[user]}, 10),
            "popularity": [m for m in popularity if str(m["id"]) not in history[user]][:10],
        }
        for method, results in recommendations.items():
            ids = {m["id"] for m in results}
            hits = len(ids & positives[user])
            measured[method].append((hits / 10, hits / len(positives[user])))
            coverage[method].update(ids)
    scores = {}
    for method, rows in measured.items():
        scores[method] = {
            "precision_at_10": float(np.mean([r[0] for r in rows])) if rows else None,
            "recall_at_10": float(np.mean([r[1] for r in rows])) if rows else None,
            "catalog_coverage": len(coverage[method]) / len(seen_ids),
        }
    return {
        "protocol": (
            "Global timestamp 80/20 split; >=5 train ratings; "
            ">=1 held-out rating >=4 in train catalog"
        ),
        "cutoff": cutoff,
        "train_ratings": len(train),
        "test_ratings": len(test),
        "eligible_users": len(eligible),
        "excluded_test_users": len({r["user_id"] for r in test}) - len(eligible),
        "candidate_movies": len(seen_ids),
        "k": 10,
        "results": scores,
        "scope": "Offline retrieval experiment, not a measure of live engagement.",
    }


def main():
    from pathlib import Path

    logging.basicConfig(level=logging.INFO)
    with Session(get_engine()) as db:
        provenance = db.scalar(select(DatasetImport))
        folder = Path("/artifacts")
        folder.mkdir(exist_ok=True)
        path = folder / "catalog.json"
        if path.exists():
            old = json.loads(path.read_text())
            if (
                old.get("sha256") == provenance.sha256
                and old.get("method") == "cosine-item-knn-hybrid-v1"
            ):
                logging.info("Model artifact already built for this archive")
                return
        genres = defaultdict(list)
        for movie_id, genre in db.execute(select(MovieGenre.movie_id, MovieGenre.genre)):
            genres[movie_id].append(genre)
        movies = [
            {"id": m.id, "title": m.title, "genres": sorted(genres[m.id])}
            for m in db.scalars(select(Movie).order_by(Movie.id))
        ]
        ratings = [
            {
                "user_id": r.user_id,
                "movie_id": r.movie_id,
                "rating": r.rating,
                "rated_at": r.rated_at,
            }
            for r in db.scalars(select(DatasetRating))
        ]
        logging.info("Building sparse item neighbors")
        catalog = build_catalog(movies, ratings)
        logging.info("Evaluating temporal holdout against popularity baseline")
        catalog["evaluation"] = evaluate(movies, ratings)
        catalog["sha256"] = provenance.sha256
        catalog["built_at"] = datetime.now(UTC).isoformat()
        catalog["source"] = "https://grouplens.org/datasets/movielens/latest/"
        temporary = folder / "catalog.partial"
        temporary.write_text(json.dumps(catalog, separators=(",", ":")))
        temporary.replace(path)
        (folder / "evaluation.json").write_text(json.dumps(catalog["evaluation"], indent=2))
        logging.info("Evaluation: %s", json.dumps(catalog["evaluation"]))


if __name__ == "__main__":
    main()
