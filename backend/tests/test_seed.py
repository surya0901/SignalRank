import zipfile

import pytest
from sqlalchemy import func, select

from app.models import DatasetImport, DatasetRating, Movie
from app.seed import import_archive, parse_archive


def test_parses_csv_quoted_titles_and_missing_genres(archive):
    movies, genres, links, ratings = parse_archive(archive)
    assert movies[0]["title"] == "Example, The (2000)"
    assert genres == [{"name": "Comedy"}, {"name": "Drama"}]
    assert all(link["movie_id"] == 1 for link in links)
    assert ratings[0]["rating"] == 4.5


def test_import_is_idempotent(db, archive):
    first = import_archive(db, archive, "https://example.test/fixture.zip")
    db.commit()
    second = import_archive(db, archive, "https://example.test/fixture.zip")
    assert first["status"] == "imported"
    assert second["status"] == "already_imported"
    assert db.scalar(select(func.count()).select_from(Movie)) == 2
    assert db.scalar(select(func.count()).select_from(DatasetRating)) == 2
    assert db.scalar(select(func.count()).select_from(DatasetImport)) == 1


def test_checksum_failure_writes_nothing(db, archive):
    with pytest.raises(ValueError, match="SHA-256"):
        import_archive(db, archive, "fixture", "0" * 64)
    assert db.scalar(select(func.count()).select_from(Movie)) == 0


def test_different_archive_cannot_mix_versions(db, archive, tmp_path):
    import_archive(db, archive, "fixture")
    db.commit()
    changed = tmp_path / "changed.zip"
    changed.write_bytes(archive.read_bytes() + b"different")
    with pytest.raises(ValueError, match="different dataset"):
        import_archive(db, changed, "fixture")


@pytest.mark.parametrize("rating", ["0", "5.5", "3.25", "nan", "inf"])
def test_invalid_ratings_are_rejected(tmp_path, rating):
    path = tmp_path / "invalid.zip"
    with zipfile.ZipFile(path, "w") as output:
        output.writestr("ml-latest-small/movies.csv", "movieId,title,genres\n1,Movie,Drama\n")
        output.writestr(
            "ml-latest-small/ratings.csv", f"userId,movieId,rating,timestamp\n1,1,{rating},1000\n"
        )
    with pytest.raises(ValueError, match="Invalid"):
        parse_archive(path)


def test_rollback_leaves_no_partial_import(db, archive):
    import_archive(db, archive, "fixture")
    db.rollback()
    assert db.scalar(select(func.count()).select_from(Movie)) == 0
    assert db.scalar(select(func.count()).select_from(DatasetImport)) == 0
