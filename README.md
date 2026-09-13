# SignalRank

Personalized movie discovery with recommendations you can understand.

SignalRank combines item-based collaborative filtering, genre preferences, and smoothed
community ratings in a responsive navy-and-cyan interface. Search the catalog, rate movies,
like discoveries, save a collection, and inspect what shaped each recommendation.

## Two ways to run

| | Public portfolio demo | Full-stack application |
| --- | --- | --- |
| Interface | React, TypeScript, Vite, Tailwind | Same interface |
| Model training | Python and scikit-learn, performed offline | Python and scikit-learn, initialization job |
| Recommendation ranking | Browser, from exported item-neighbor artifact | Browser feed plus equivalent FastAPI recommendation endpoint |
| Preferences | Local to each visitor's browser | Isolated sessions in PostgreSQL |
| Account | No signup required | No signup; demo session expires after seven days |
| Runtime | Static hosting | Docker Compose: Nginx, FastAPI, PostgreSQL |

**The shareable demo does not host FastAPI or PostgreSQL.** It uses a real trained model
artifact and the same ranking formula. The containerized full-stack application is included
for local operation and a future server deployment. No API hosting or live engagement claim
is implied by the public demo. See [deployment notes](docs/deployment.md) for verified status.

## Features

- For You feed, community picks, recent catalog releases, and saved collection.
- Search by movie title or genre, genre filters, and incremental results.
- Half-star ratings, likes, saves, and editable genre preferences.
- Five clearly disclosed example ratings so a new visitor immediately sees personalization.
- Restore the example taste or start from a blank profile.
- Recommendation explanations tied to actual ranking contributions.
- Analytics calculated from the catalog, current profile, and a real offline evaluation.
- Responsive layout with desktop sidebar and mobile navigation, labeled controls, keyboard
  focus states, loading/error/retry states, and reduced-motion support.

The movie artwork is atmospheric photography, not official posters. No generated synopses,
streaming availability, current trending claims, or fictional engagement metrics are used.

## One-command full-stack startup

Install and start Docker Desktop (or Docker Engine with Compose), then run:

```sh
docker compose up --build -d
```

- App: http://localhost:3000
- Swagger docs: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json

The first run downloads images/dependencies and MovieLens, applies Alembic migrations,
imports data transactionally, builds sparse item neighbors, and evaluates a separate model
on held-out ratings. API startup waits for successful initialization. Later runs reuse the
cached dataset and artifact. Initial startup requires internet access and can take minutes.

Database credentials are generated into a Docker volume and are never stored in the repo.
PostgreSQL is not exposed on a host port; the app and API bind to loopback only. Copy
`.env.example` to `.env` for optional port/configuration changes. Never put secrets in a
`VITE_` setting, because those values are public in the browser bundle.

```sh
docker compose ps -a
docker compose logs init
docker compose logs api
docker compose down
```

`down` retains data. **`docker compose down -v` permanently deletes database contents,
credentials, and artifacts.** Use it only for an intentional reset. Do not delete only the
credential volume while retaining the database that expects its original password.

## Public-demo build

The checked-in `frontend/public/data/catalog.json` contains movie metadata, aggregate rating
statistics, sparse item-neighbor similarities, and measured evaluation results. It contains
no raw user-rating matrix or application sessions. It was produced by the Python pipeline.

```sh
npm --prefix frontend ci
npm run build
```

The root build enables portable-demo mode and stages the static site in `dist/`. To preview
that build, serve `dist/` using a static server. To develop against the live Compose API:

```sh
cd frontend
npm run dev
```

Vite proxies `/api` to `127.0.0.1:8000`. Adjust that proxy and `ALLOWED_ORIGINS` if you change
ports. In Compose, Nginx serves the production frontend and proxies `/api` on the same origin.

## Structure

```text
frontend/
  src/              UI, browser ranking, persistence adapter, tests
  public/artwork/   Attributed atmosphere photographs
  public/data/      Exported model/catalog artifact for portable demo
backend/
  app/              API, sessions, ingestion, recommendation model, evaluation
  alembic/          Versioned PostgreSQL migrations
  tests/            Ingestion, auth/isolation, validation, recommendation tests
docs/
  architecture.md   Data flow, formulas, evaluation protocol, tradeoffs
  evaluation.json   Actual offline evaluation report
  ranking-parity.json  Python results used to verify browser equivalence
  testing.md        Local verification record
  deployment.md     Public-demo versus server-hosting scope
scripts/            Credential initialization, smoke test, public build/staging
compose.yaml        Health-gated local stack
.env.example        Nonsecret configuration examples
```

## Recommendation approach

Item vectors contain `max(rating − 2.5, 0)` for each public MovieLens viewer. scikit-learn
cosine nearest neighbors retrieves up to 40 related items. Inference combines:

1. **Similarity (0.60):** normalized contributions from positively weighted rated, liked,
   and saved reference movies.
2. **Genre affinity (0.25):** genre preferences from explicit choices and movie interactions;
   low ratings can reduce affinity.
3. **Community quality (0.15):** movie mean smoothed toward the dataset mean with 20 prior
   ratings, then scaled to the five-star range.

A rating contributes `(rating − 3) / 2`; likes add 0.6 and saves add 0.35. Explicit genre
choices add 2 to their genre. Already-rated movies are excluded from For You. Stable tie
breaking uses rating count then movie ID. The weights are design choices, not measured
causal effects, probabilities, or tuned performance guarantees.

See [architecture](docs/architecture.md) for the full formula and limitations.

## Measured offline results

The current artifact uses a global timestamp 80/20 split: 80,669 training ratings and 20,167
held-out ratings. Only training data determines neighbors, community statistics, and the
candidate catalog. A relevant test item has a rating ≥4 and exists in the training catalog.
A user must have ≥5 training ratings and ≥1 relevant held-out item. **28 users qualify; 88
test users are excluded.** This small, selective cohort limits generalization.

| Metric | SignalRank hybrid | Smoothed popularity |
| --- | ---: | ---: |
| Precision@10 | 0.110714 | 0.082143 |
| Recall@10 | 0.065259 | 0.032983 |
| Catalog coverage | 0.020465 | 0.006356 |

These are observed offline results for this archive and protocol, not production engagement
or a claim that the method universally outperforms a baseline. There was no hyperparameter
search. The deployed-demo artifact is fitted on all available data after a separate evaluation.

## API

| Method | Route | Behavior |
| --- | --- | --- |
| GET | `/health/live`, `/health/ready` | Process/database and import readiness |
| GET | `/api/dataset` | Database-derived dataset metadata |
| POST | `/api/auth/demo` | Create/reuse an isolated HttpOnly-cookie demo session |
| GET / PUT | `/api/me` | Read/update validated ratings, likes, saves, genre preferences |
| DELETE | `/api/auth/session` | Revoke the current demo session |
| GET | `/api/catalog` | Exported model and catalog |
| GET | `/api/movies?q=&genre=&offset=0&limit=24` | Search with pagination |
| GET | `/api/recommendations?limit=24` | Authenticated personalized results and explanations |
| GET | `/api/analytics` | Authenticated user counts and actual evaluation |

Writes check Origin, preferences validate movie/genre IDs and half-star rating increments,
and session tokens are stored as hashes. Expired profiles are cleaned when new demos start.
A bounded in-process limiter limits new sessions; a publicly hosted API would need shared
rate limiting, HTTPS-aware secure cookies, backups, monitoring, and deployment review.

## Tests

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
cd backend
../.venv/bin/pytest -q
../.venv/bin/ruff check .
```

```sh
npm --prefix frontend test
npm run build
python3 scripts/smoke.py
```

Unit tests use clearly synthetic fixtures. Browser/Python parity tests use the actual exported
model and three different preference profiles. The smoke test uses the running PostgreSQL
stack, validates independent sessions and persistence, and exercises the recommendation API.
See [verification record](docs/testing.md) for actual outcomes and warnings.

## Rebuilding artifacts

```sh
docker compose exec api python -c "from pathlib import Path; Path('/artifacts/catalog.json').unlink(missing_ok=True)"
docker compose exec api python -m app.train
docker compose cp api:/artifacts/catalog.json frontend/public/data/catalog.json
docker compose cp api:/artifacts/evaluation.json docs/evaluation.json
```

Restart the API after replacing an artifact (its loader caches one version). Model artifacts
are not automatically rebuilt on every user action; ranking applies current preferences
immediately. Regenerate parity fixtures if you intentionally change the algorithm.

## Dataset and artwork

[MovieLens latest-small](https://grouplens.org/datasets/movielens/latest/) is provided by
GroupLens. The original archive and README are retained in the dataset volume. The archive
SHA-256 is pinned to the checksum published by
[TensorFlow Datasets](https://raw.githubusercontent.com/tensorflow/datasets/master/tensorflow_datasets/url_checksums/movielens.txt):
`696d65a3dfceac7c45750ad32df2c259311949efec81f0f144fdfb91ebc9e436`.

The primary download server had an expired certificate during testing. The importer uses
an HTTPS mirror only for that exact checksum; TLS verification is never disabled. Custom
URLs do not silently fall back. No raw MovieLens ratings are committed. Retain attribution
and review the original terms before redistribution or commercial use.

Atmosphere photography: [Leo_Visions](https://unsplash.com/pt-br/fotografias/uma-estrada-que-atravessa-um-campo-sob-um-ceu-noturno-cheio-de-estrelas-NODGBBt370E),
[Aleksandr Popov](https://unsplash.com/photos/blue-and-black-high-rise-building-GmLfS_S43gA),
and [Francesco Ungaro](https://unsplash.com/photos/a-body-of-water-with-a-light-shining-on-it-CB08mpb-ync).
See the [Unsplash license](https://unsplash.com/license).

## Screenshots

- Placeholder: desktop personalized feed and explanation panel.
- Placeholder: mobile discovery and saved collection.
- Placeholder: analytics with the recorded offline evaluation.

## Limitations and future work

The catalog ends in 2018. Availability and popularity are historical. Implicit interests are
approximations, and offline evaluation is affected by selection bias. Demo browser preferences
do not sync between devices. API sessions are temporary. This is not a streaming service.
Future work includes diversity-aware reranking, larger-scale retrieval, account-based sync,
versioned artifact rollout, and properly designed online evaluation if real traffic exists.
