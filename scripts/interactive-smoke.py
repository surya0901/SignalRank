"""Exercise actual PostgreSQL sessions, mutations and recommendations; revoke test profiles."""

import http.cookiejar
import json
import urllib.request
from urllib.error import URLError

BASE = "http://127.0.0.1:3000"


def client():
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )


def call(opener, path, method="GET", data=None):
    request = urllib.request.Request(
        BASE + path,
        method=method,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type": "application/json", "Origin": BASE},
    )
    with opener.open(request, timeout=30) as response:
        content = response.read()
        return json.loads(content) if content else None


first, second = client(), client()
try:
    original = call(first, "/api/auth/demo", "POST")
    other = call(second, "/api/auth/demo", "POST")
    recommendations = call(first, "/api/recommendations")["items"]
    chosen = recommendations[0]["id"]
    assert all(str(m["id"]) not in original["ratings"] for m in recommendations)
    changed = {
        **original,
        "saved": [chosen],
        "liked": [chosen],
        "ratings": {**original["ratings"], str(chosen): 4.5},
    }
    call(first, "/api/me", "PUT", changed)
    assert call(first, "/api/me") == changed
    assert call(second, "/api/me") == other
    assert chosen not in {m["id"] for m in call(first, "/api/recommendations")["items"]}
    assert call(first, "/api/movies?q=Matrix")["total"] > 0
    metrics = call(first, "/api/analytics")
    assert metrics["your_saves"] == 1
    assert metrics["evaluation"]["eligible_users"] > 0
    print(
        "Passed: independent sessions, persistence, ratings, likes, saves, search, recommendations, analytics."
    )
finally:
    for opener in [first, second]:
        try:
            call(opener, "/api/auth/session", "DELETE")
        except URLError:
            print("Test profile cleanup unavailable; the session will expire automatically.")
