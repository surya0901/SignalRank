import hashlib
import io
import urllib.error

import pytest

from app import seed
from app.config import MOVIELENS_MIRROR, MOVIELENS_URL


class Response(io.BytesIO):
    def geturl(self):
        return "https://example.test/archive.zip"


def test_verified_download_is_atomic(tmp_path, monkeypatch):
    data = b"verified test bytes"
    checksum = hashlib.sha256(data).hexdigest()
    monkeypatch.setattr(seed.urllib.request, "urlopen", lambda *a, **kw: Response(data))
    target = tmp_path / "archive.zip"
    assert seed.download_archive(target, "https://example.test/archive.zip", checksum)
    assert target.read_bytes() == data
    assert not target.with_suffix(".partial").exists()


def test_bad_checksum_leaves_no_cached_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(seed.urllib.request, "urlopen", lambda *a, **kw: Response(b"tampered"))
    target = tmp_path / "archive.zip"
    with pytest.raises(ValueError, match="SHA-256"):
        seed.download_archive(target, MOVIELENS_URL, seed.MOVIELENS_SHA256)
    assert not target.exists()
    assert not target.with_suffix(".partial").exists()


def test_https_failure_uses_checksum_verified_mirror(tmp_path, monkeypatch):
    data = b"fixture standing in for the pinned archive"
    checksum = hashlib.sha256(data).hexdigest()
    monkeypatch.setattr(seed, "MOVIELENS_SHA256", checksum)
    calls = []

    def open_url(url, **kwargs):
        calls.append(url)
        if url == MOVIELENS_URL:
            raise urllib.error.URLError("certificate expired")
        return Response(data)

    monkeypatch.setattr(seed.urllib.request, "urlopen", open_url)
    seed.download_archive(tmp_path / "archive.zip", MOVIELENS_URL, checksum)
    assert calls == [MOVIELENS_URL, MOVIELENS_MIRROR]


def test_custom_source_does_not_silently_fall_back(tmp_path, monkeypatch):
    calls = []

    def fail(url, **kwargs):
        calls.append(url)
        raise urllib.error.URLError("unavailable")

    monkeypatch.setattr(seed.urllib.request, "urlopen", fail)
    with pytest.raises(urllib.error.URLError):
        seed.download_archive(tmp_path / "archive.zip", "https://example.test/custom.zip", "0" * 64)
    assert len(calls) == 1
