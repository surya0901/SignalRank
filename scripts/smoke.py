"""Verify the running Compose foundation without modifying its data."""

import argparse
import json
import urllib.request


def get(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        assert response.status == 200, url
        return response.read().decode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--web", default="http://127.0.0.1:3000")
    args = parser.parse_args()
    assert json.loads(get(args.api + "/health/live"))["status"] == "ok"
    assert json.loads(get(args.api + "/health/ready"))["status"] == "ready"
    schema = json.loads(get(args.api + "/openapi.json"))
    assert "/api/dataset" in schema["paths"]
    assert "swagger-ui" in get(args.api + "/docs")
    direct = json.loads(get(args.api + "/api/dataset"))
    proxied = json.loads(get(args.web + "/api/dataset"))
    assert direct == proxied, "Frontend proxy and direct API returned different data"
    for key in ["movies", "ratings", "users", "genres"]:
        assert isinstance(direct[key], int) and direct[key] > 0, key
    assert len(direct["sha256"]) == 64
    assert "SignalRank" in get(args.web + "/")
    assert "<svg" in get(args.web + "/favicon.svg")
    print(json.dumps({"status": "passed", "dataset": direct}, indent=2))


if __name__ == "__main__":
    main()
