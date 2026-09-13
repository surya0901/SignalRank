# Local verification

This file records tests actually run, distinct from planned checks and model measurements.

## Phase 1

Verified locally on September 13, 2026, on macOS/Apple Silicon with Docker Desktop
29.7.2, Compose 5.4.0, and PostgreSQL 17.11. This is local verification, not deployment.

| Check | Observed result |
| --- | --- |
| Backend unit tests, host Python 3.12 | 16 passed |
| Backend unit tests, Linux container | 16 passed |
| Backend/script lint and format checks | Passed |
| Frontend Vitest tests | 2 passed |
| TypeScript and Vite production build | Passed locally and in Docker |
| npm dependency audit after test-runner update | 0 reported vulnerabilities at test time |
| Compose configuration | Valid |
| Container startup and PostgreSQL migration | Passed |
| Alembic model/schema consistency check | No new upgrade operations detected |
| Direct API, Swagger/OpenAPI, frontend proxy smoke checks | Passed |
| Repeat initialization | `already_imported`; original rows retained |
| Desktop browser review | Real counts rendered in navy/cyan layout |
| Phone browser review, 390 × 844 | Real counts rendered; no horizontal overflow observed |

The test client currently emits two third-party deprecation warnings (httpx and AnyIO).
The container test also emitted a cache-write warning because `/app` is not writable by the
application user. None failed a test. Use `pytest -p no:cacheprovider` inside the container
to avoid the optional test cache warning. These checks are not a security certification.

### Actual imported data

- Movies: 9,742
- Ratings: 100,836
- Distinct public dataset users: 610
- Named genres: 19 (the dataset's 'no genres listed' marker is not treated as a genre)
- Archive SHA-256: `696d65a3dfceac7c45750ad32df2c259311949efec81f0f144fdfb91ebc9e436`
- Source used: `https://raw.githubusercontent.com/neaorin/databricks-workshop/master/data/ml-latest-small.zip`
- Import timestamp: `2026-09-13T18:09:24.015238+00:00`

The first startup failed because the primary GroupLens server's certificate was expired.
The importer was fixed to use a TLS-verified HTTPS mirror only for the independently
checksum-pinned archive. The successful startup above exercised this fallback. No TLS
validation was disabled; no mock dataset substituted for MovieLens.

### Reproduce

```sh
docker compose up --build -d
python3 scripts/smoke.py
docker compose exec -T api pytest -q -p no:cacheprovider
docker compose exec -T api alembic check
docker compose run --rm --no-deps init
```

From `frontend/`, run `npm ci`, `npm test`, and `npm run build`.

The backend suite checks archive parsing, invalid ratings, checksum enforcement, version
mixing, repeat imports, transactional rollback, health checks, and API-derived counts.
The frontend suite checks data returned by the API and recovery from a failed request.

The Compose check built real containers, applied migrations to PostgreSQL, imported the
public archive, queried the API through both direct and frontend proxy routes, and verified
repeated initialization. Unit fixtures are synthetic test data, never displayed as MovieLens
statistics or used to claim recommendation quality.

No recommendation evaluation or public deployment has occurred in this phase.

## Completed interactive demo

The final suite now covers isolated demo profiles, session revocation, origin checks,
validation, search pagination, cold-start ranking, saved-content effects, and explanation
contributions. Browser-side tests cover search, saving, rating-driven feed changes, retry,
three Python/TypeScript ranking comparisons, and finite/no-self-neighbor invariants.

- Backend: 25 tests passed locally.
- Frontend: 8 tests passed locally.
- Actual model evaluation is recorded in `evaluation.json`; it is no longer unrun.
- The earlier phase-1 result remains historical; it does not describe the finished interface.
- Final Compose, public build, and deployment verification are recorded below when complete.

### Final local verification — 2026-09-13

- Docker Compose rebuilt and started successfully; PostgreSQL and API health checks passed.
- Backend suite inside the final API image: 25 passed, two dependency deprecation warnings.
- Production frontend build and portable public build both completed successfully.
- Live integration checks passed: independent sessions, persistence, ratings, likes, saves, search, recommendations, analytics, and session cleanup.
- Catalog confirmed from PostgreSQL: 9,742 movies, 100,836 ratings, 610 users.

- Public deployment succeeded. Anonymous HTTPS checks passed for HTML, JavaScript, CSS, and the 9,742-movie catalog. See [deployment notes](deployment.md).
