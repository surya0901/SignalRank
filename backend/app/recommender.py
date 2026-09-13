"""Sparse collaborative retrieval with explicit, inspectable ranking contributions."""

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from sklearn.neighbors import NearestNeighbors


def build_catalog(movies: list[dict], ratings: list[dict], neighbors: int = 40) -> dict:
    ids = [m["id"] for m in movies]
    positions = {movie_id: index for index, movie_id in enumerate(ids)}
    users = {u: i for i, u in enumerate(sorted({r["user_id"] for r in ratings}))}
    relevant = [r for r in ratings if r["movie_id"] in positions]
    matrix = coo_matrix(
        (
            [max(0, r["rating"] - 2.5) for r in relevant],
            ([positions[r["movie_id"]] for r in relevant], [users[r["user_id"]] for r in relevant]),
        ),
        shape=(len(ids), len(users)),
    ).tocsr()
    matrix.eliminate_zeros()
    model = NearestNeighbors(metric="cosine", algorithm="brute", n_jobs=1).fit(matrix)
    sums, counts = np.zeros(len(ids)), np.zeros(len(ids))
    for rating in relevant:
        i = positions[rating["movie_id"]]
        sums[i] += rating["rating"]
        counts[i] += 1
    global_mean = float(sums.sum() / max(1, counts.sum()))
    enriched = []
    # Batches avoid allocating a dense full item-by-item distance matrix.
    for start in range(0, len(ids), 256):
        distances, indices = model.kneighbors(
            matrix[start : start + 256], n_neighbors=min(neighbors + 1, len(ids))
        )
        for offset, (distance, index) in enumerate(zip(distances, indices, strict=True)):
            i = start + offset
            related = sorted(
                [
                    (ids[int(j)], round(float(1 - d), 6))
                    for j, d in zip(index, distance, strict=True)
                    if j != i and 1 - d > 0.000001
                ],
                key=lambda pair: (-pair[1], pair[0]),
            )[:neighbors]
            enriched.append(
                {
                    **movies[i],
                    "count": int(counts[i]),
                    "mean": round(float(sums[i] / counts[i]), 3) if counts[i] else None,
                    "quality": round(float((sums[i] + 20 * global_mean) / (counts[i] + 20) / 5), 6),
                    "neighbors": related,
                }
            )
    return {
        "movies": enriched,
        "rating_count": len(relevant),
        "user_count": len(users),
        "method": "cosine-item-knn-hybrid-v1",
        "neighbors": neighbors,
    }


DEMO_RATINGS = {"1": 4.5, "260": 5, "2571": 4.5, "2959": 4, "4993": 5}


def rank(catalog: dict, state: dict, limit: int = 24) -> list[dict]:
    movies = catalog["movies"]
    ratings = state.get("ratings", {})
    saved, liked = set(state.get("saved", [])), set(state.get("liked", []))
    genre_weights: dict[str, float] = {}
    collaborative: dict[int, float] = {}
    references: dict[int, tuple[float, str]] = {}
    explicit_genres = state.get("genres", [])
    for genre in explicit_genres:
        genre_weights[genre] = genre_weights.get(genre, 0) + 2
    for movie in movies:
        rating = ratings.get(str(movie["id"]))
        weight = (float(rating) - 3) / 2 if rating is not None else 0
        weight += 0.6 * (movie["id"] in liked) + 0.35 * (movie["id"] in saved)
        if not weight:
            continue
        for genre in movie["genres"]:
            genre_weights[genre] = genre_weights.get(genre, 0) + weight
        if weight > 0:
            for related_id, similarity in movie["neighbors"]:
                contribution = weight * similarity
                collaborative[related_id] = collaborative.get(related_id, 0) + contribution
                if contribution > references.get(related_id, (0, ""))[0]:
                    references[related_id] = (contribution, movie["title"])
    max_collab = max(collaborative.values(), default=1) or 1
    max_genre = max([abs(x) for x in genre_weights.values()], default=1) or 1
    ranked = []
    for movie in movies:
        if str(movie["id"]) in ratings:
            continue
        affinity = sum(genre_weights.get(g, 0) for g in movie["genres"])
        affinity /= max(1, len(movie["genres"])) * max_genre
        signals = {
            "similarity": round(0.6 * collaborative.get(movie["id"], 0) / max_collab, 6),
            "genres": round(0.25 * max(-1, affinity), 6),
            "community": round(0.15 * movie["quality"], 6),
        }
        explanation = f"Community pick from {movie['count']} MovieLens ratings"
        if signals["similarity"] > 0:
            explanation = f"Similar viewing patterns to {references[movie['id']][1]}"
        elif affinity > 0:
            matches = [g for g in movie["genres"] if genre_weights.get(g, 0) > 0]
            explanation = f"Matches your interest in {', '.join(matches[:2])}"
        ranked.append(
            {
                **movie,
                "score": round(sum(signals.values()), 6),
                "signals": signals,
                "explanation": explanation,
            }
        )
    return sorted(ranked, key=lambda m: (-m["score"], -m["count"], m["id"]))[:limit]


@lru_cache(maxsize=1)
def load_catalog(path: str = "/artifacts/catalog.json") -> dict:
    return json.loads(Path(path).read_text())
