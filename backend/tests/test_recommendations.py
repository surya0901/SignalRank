import pytest

from app.recommender import build_catalog, rank


@pytest.fixture
def catalog():
    movies = [
        {"id": i, "title": f"Movie {i}", "genres": ["Drama" if i < 3 else "Comedy"]}
        for i in range(1, 5)
    ]
    ratings = [
        {"user_id": u, "movie_id": m, "rating": 5 if m < 3 else 2, "rated_at": 1000 + u * 10 + m}
        for u in range(1, 4)
        for m in range(1, 5)
    ]
    return build_catalog(movies, ratings, 3)


def test_rated_items_are_excluded_and_similar_items_explained(catalog):
    results = rank(catalog, {"ratings": {"1": 5}})
    assert all(m["id"] != 1 for m in results)
    assert results[0]["id"] == 2
    assert "Movie 1" in results[0]["explanation"]
    assert results[0]["signals"]["similarity"] > 0


def test_saved_content_changes_ranking(catalog):
    result = rank(catalog, {"saved": [1], "ratings": {}})
    assert result[0]["id"] == 2
    assert result[0]["signals"]["similarity"] > 0


def test_cold_start_has_no_invented_personalization(catalog):
    result = rank(catalog, {})
    assert all("Community pick" in m["explanation"] for m in result)
    assert all(m["signals"]["similarity"] == 0 for m in result)


def test_scores_are_the_sum_of_explained_signals(catalog):
    for movie in rank(catalog, {"genres": ["Comedy"], "ratings": {"1": 0.5}}):
        assert movie["score"] == pytest.approx(sum(movie["signals"].values()), abs=1e-6)
