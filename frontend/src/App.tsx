import { useEffect, useMemo, useState } from "react";
import Icon from "./Icon";
import { loadData, persist, portable } from "./data";
import {
  Catalog,
  Movie,
  Preferences,
  Ranked,
  emptyPreferences,
  initialPreferences,
  rank,
  title,
  year,
} from "./engine";

type Page =
  "home" | "explore" | "personalize" | "saved" | "analytics" | "model";
const nav: [Page, string, string][] = [
  ["home", "Home", "home"],
  ["explore", "Explore", "explore"],
  ["personalize", "Personalize", "sliders"],
  ["analytics", "Analytics", "chart"],
  ["saved", "Saved", "bookmark"],
  ["model", "The model", "model"],
];
const format = (n: number) => n.toLocaleString();
const percent = (n: number | null) =>
  n === null ? "Not evaluated" : `${(n * 100).toFixed(2)}%`;
const art = (m: Movie) =>
  m.genres.some((g) => ["Sci-Fi", "Fantasy", "Western"].includes(g))
    ? "mountain-night"
    : m.genres.some((g) =>
          ["Adventure", "Animation", "Documentary"].includes(g),
        )
      ? "ocean-depths"
      : "city-night";
const ratingOptions = Array.from({ length: 10 }, (_, i) => (i + 1) / 2);

export default function App() {
  const [catalog, setCatalog] = useState<Catalog | null>(null),
    [preferences, setPreferences] = useState<Preferences>(initialPreferences);
  const [page, setPage] = useState<Page>("home"),
    [tab, setTab] = useState("For You"),
    [query, setQuery] = useState(""),
    [genre, setGenre] = useState("All genres");
  const [selected, setSelected] = useState<number | null>(null),
    [shown, setShown] = useState(12),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(""),
    [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setError("");
    loadData()
      .then(([data, p]) => {
        if (active) {
          setCatalog(data);
          setPreferences(p);
        }
      })
      .catch(() => {
        if (active)
          setError("We couldn’t load the movie catalog. Please try again.");
      });
    return () => {
      active = false;
    };
  }, [attempt]);
  useEffect(() => {
    if (!notice) return;
    const t = window.setTimeout(() => setNotice(""), 3500);
    return () => clearTimeout(t);
  }, [notice]);
  useEffect(() => setShown(12), [page, query, genre, tab]);
  const ranked = useMemo(
    () => (catalog ? rank(catalog, preferences) : []),
    [catalog, preferences],
  );
  const rankedMap = useMemo(
    () => new Map(ranked.map((m) => [m.id, m])),
    [ranked],
  );
  const genres = useMemo(
    () => [...new Set(catalog?.movies.flatMap((m) => m.genres) || [])].sort(),
    [catalog],
  );
  const filtered = useMemo(() => {
    if (!catalog) return [];
    let movies: Movie[] =
      page === "home" && tab === "For You" && !query ? ranked : catalog.movies;
    if (page === "saved" || (page === "home" && tab === "Saved"))
      movies = movies.filter((m) => preferences.saved.includes(m.id));
    else if (page === "home" && tab === "Recent")
      movies = [...movies].sort(
        (a, b) => Number(year(b)) - Number(year(a)) || b.count - a.count,
      );
    else if (page !== "home" || tab !== "For You" || query)
      movies = [...movies].sort(
        (a, b) => b.quality - a.quality || b.count - a.count,
      );
    return movies.filter(
      (m) =>
        (!query ||
          `${m.title} ${m.genres.join(" ")}`
            .toLowerCase()
            .includes(query.toLowerCase())) &&
        (genre === "All genres" || m.genres.includes(genre)),
    );
  }, [catalog, ranked, page, tab, query, genre, preferences.saved]);
  const activeMovie =
    catalog?.movies.find((m) => m.id === selected) || filtered[0];
  async function update(next: Preferences, message: string) {
    if (busy) return;
    setBusy(true);
    try {
      await persist(next);
      setPreferences(next);
      setNotice(message);
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Unable to save changes.");
    } finally {
      setBusy(false);
    }
  }
  const toggle = (kind: "saved" | "liked", id: number) =>
    update(
      {
        ...preferences,
        [kind]: preferences[kind].includes(id)
          ? preferences[kind].filter((x) => x !== id)
          : [...preferences[kind], id],
      },
      kind === "saved"
        ? "Your collection is updated."
        : "Your preferences are updated.",
    );
  function navigate(next: Page) {
    setPage(next);
    setQuery("");
    setGenre("All genres");
    setSelected(null);
  }
  function rate(id: number, value: string) {
    const ratings = { ...preferences.ratings };
    if (value) ratings[id] = Number(value);
    else delete ratings[id];
    void update(
      { ...preferences, ratings },
      "Rating saved. Your feed is updated.",
    );
  }
  const pageNames = {
    home: "For You",
    explore: "Explore",
    personalize: "Make it yours",
    saved: "Your collection",
    analytics: "The numbers behind it",
    model: "A closer look",
  };
  const subtitles = {
    home: "Personalized picks, powered by what you care about.",
    explore: "A different world. A new perspective. Your next favorite.",
    personalize: "Start with what you love. Let your next discovery follow.",
    saved: "Good discoveries deserve a place to stay.",
    analytics: "Real data. Measured results. No mystery numbers.",
    model: "Recommendations you can understand.",
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            navigate("home");
          }}
        >
          <span className="brand-orb" />
          <span>
            SignalRank<small>Discover what moves you.</small>
          </span>
        </a>
        <div className="nav-label">YOUR DISCOVERY</div>
        <nav aria-label="Main navigation">
          {nav.map(([id, label, icon]) => (
            <button
              key={id}
              className={`nav-item ${page === id ? "active" : ""}`}
              aria-current={page === id ? "page" : undefined}
              onClick={() => navigate(id)}
            >
              <Icon name={icon} />
              <span>{label}</span>
              {id === "saved" && preferences.saved.length > 0 && (
                <b>{preferences.saved.length}</b>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="signal-mark">
            <i />
            <i />
            <i />
            <i />
          </div>
          <strong>A little more you.</strong>
          <p>
            Every rating helps shape
            <br />
            what you discover next.
          </p>
          <span>Built on MovieLens</span>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="mobile-brand">
            <span className="brand-orb" />
            SignalRank
          </div>
          <label className="search">
            <Icon name="search" size={18} />
            <input
              aria-label="Search movies"
              placeholder="Search movies, genres, or a new favorite…"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                if (!["home", "explore", "saved"].includes(page))
                  setPage("explore");
              }}
            />
            {query && (
              <button aria-label="Clear search" onClick={() => setQuery("")}>
                <Icon name="close" size={16} />
              </button>
            )}
          </label>
          <button
            className="profile-pill"
            onClick={() => navigate("personalize")}
          >
            <span className="avatar">S</span>
            <span>
              Demo profile
              <small>
                {portable ? "Saved in this browser" : "Your own session"}
              </small>
            </span>
            <Icon name="chevron" size={14} />
          </button>
        </header>
        <main>
          {error ? (
            <div className="empty" role="alert">
              <Icon name="info" size={32} />
              <h1>Let’s reconnect.</h1>
              <p>{error}</p>
              <button
                className="primary"
                onClick={() => setAttempt((x) => x + 1)}
              >
                Try again
              </button>
            </div>
          ) : !catalog ? (
            <div className="empty" role="status">
              <span className="loader" />
              <h1>Finding your next favorite…</h1>
              <p>Loading the movie catalog.</p>
            </div>
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">
                    {page === "home"
                      ? "A WORLD WORTH DISCOVERING"
                      : "YOUR SIGNAL, EXPLAINED"}
                  </div>
                  <h1>{query ? "Search results" : pageNames[page]}</h1>
                  <p>
                    {query
                      ? `Movies and genres matching “${query}”`
                      : subtitles[page]}
                  </p>
                </div>
                {page === "home" && !query && (
                  <div className="tabs" aria-label="Feed view">
                    {["For You", "Community", "Recent", "Saved"].map((t) => (
                      <button
                        key={t}
                        className={tab === t ? "active" : ""}
                        onClick={() => setTab(t)}
                        aria-pressed={tab === t}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {["home", "explore", "saved"].includes(page) && (
                <>
                  <div className="feed-tools">
                    <div className="chips">
                      {[
                        "All genres",
                        "Sci-Fi",
                        "Adventure",
                        "Drama",
                        "Comedy",
                        "Thriller",
                      ].map((g) => (
                        <button
                          key={g}
                          className={genre === g ? "chosen" : ""}
                          onClick={() => setGenre(g)}
                        >
                          {g}
                        </button>
                      ))}
                    </div>
                    <select
                      aria-label="Filter by genre"
                      value={genre}
                      onChange={(e) => setGenre(e.target.value)}
                    >
                      <option>All genres</option>
                      {genres.map((g) => (
                        <option key={g}>{g}</option>
                      ))}
                    </select>
                  </div>
                  {page === "home" && tab === "Recent" && (
                    <p className="context-note">
                      Newest release years in the MovieLens catalog, which ends
                      in 2018.
                    </p>
                  )}
                  <div className="discovery-layout">
                    <section className="feed" aria-label="Movie feed">
                      {filtered.length === 0 ? (
                        <div className="empty compact">
                          <Icon name="bookmark" size={30} />
                          <h2>
                            {page === "saved" || tab === "Saved"
                              ? "Your next discovery belongs here."
                              : "No movies found."}
                          </h2>
                          <p>
                            Explore a different genre, or save a movie for
                            later.
                          </p>
                          <button
                            className="secondary"
                            onClick={() => {
                              navigate("explore");
                              setTab("For You");
                            }}
                          >
                            Explore movies <Icon name="arrow" size={16} />
                          </button>
                        </div>
                      ) : (
                        <div className="movie-grid">
                          {filtered.slice(0, shown).map((movie) => (
                            <article
                              key={movie.id}
                              className={`movie-card ${activeMovie?.id === movie.id ? "selected" : ""}`}
                            >
                              <button
                                className={`movie-art art-${movie.id % 4}`}
                                aria-label={`Why ${title(movie)} is recommended`}
                                onClick={() => setSelected(movie.id)}
                              >
                                <img
                                  src={`/artwork/${art(movie)}.jpg`}
                                  alt=""
                                  loading="lazy"
                                />
                                <div className="art-shade" />
                                <span className="movie-year">
                                  {year(movie)}
                                </span>
                                {!!rankedMap.get(movie.id)?.signals
                                  .similarity && (
                                  <span className="match-label">
                                    <span />
                                    For your taste
                                  </span>
                                )}
                                <div className="movie-caption">
                                  <span className="movie-genre">
                                    {movie.genres.slice(0, 2).join(" / ") ||
                                      "Cinema"}
                                  </span>
                                  <h2>{title(movie)}</h2>
                                </div>
                              </button>
                              <div className="card-info">
                                <span className="community-score">
                                  <Icon name="star" size={14} />
                                  {movie.mean?.toFixed(1) || "—"}
                                  <small>{format(movie.count)} ratings</small>
                                </span>
                                <div className="card-actions">
                                  <button
                                    disabled={busy}
                                    className={
                                      preferences.liked.includes(movie.id)
                                        ? "on"
                                        : ""
                                    }
                                    aria-label={`Like ${title(movie)}`}
                                    aria-pressed={preferences.liked.includes(
                                      movie.id,
                                    )}
                                    onClick={() => toggle("liked", movie.id)}
                                  >
                                    <Icon name="heart" size={17} />
                                  </button>
                                  <button
                                    disabled={busy}
                                    className={
                                      preferences.saved.includes(movie.id)
                                        ? "on"
                                        : ""
                                    }
                                    aria-label={`Save ${title(movie)}`}
                                    aria-pressed={preferences.saved.includes(
                                      movie.id,
                                    )}
                                    onClick={() => toggle("saved", movie.id)}
                                  >
                                    <Icon name="bookmark" size={17} />
                                  </button>
                                </div>
                              </div>
                              <label className="rating-select">
                                <span>Your rating</span>
                                <select
                                  disabled={busy}
                                  aria-label={`Rate ${title(movie)}`}
                                  value={preferences.ratings[movie.id] || ""}
                                  onChange={(e) =>
                                    rate(movie.id, e.target.value)
                                  }
                                >
                                  <option value="">Not rated</option>
                                  {ratingOptions.map((r) => (
                                    <option key={r} value={r}>
                                      {r} ★
                                    </option>
                                  ))}
                                </select>
                              </label>
                            </article>
                          ))}
                        </div>
                      )}
                      {filtered.length > shown && (
                        <button
                          className="load-more secondary"
                          onClick={() => setShown((x) => x + 12)}
                        >
                          Discover more <Icon name="arrow" size={16} />
                        </button>
                      )}
                    </section>
                    <aside className="explanation-panel">
                      <div className="panel-title">
                        <Icon name="model" />
                        <h2>Why recommended</h2>
                      </div>
                      <p className="muted">
                        A little context for your next pick.
                      </p>
                      {activeMovie ? (
                        <>
                          <div className="selected-title">
                            <span>IN FOCUS</span>
                            <h3>{title(activeMovie)}</h3>
                            <p>{activeMovie.genres.join(" · ")}</p>
                          </div>
                          <Explanation
                            movie={activeMovie}
                            ranked={rankedMap.get(activeMovie.id)}
                          />
                          <div className="panel-divider" />
                          <div className="your-signal">
                            <span>Your discovery profile</span>
                            <strong>
                              {Object.keys(preferences.ratings).length} ratings{" "}
                              <i>·</i> {preferences.saved.length} saved
                            </strong>
                          </div>
                          <button
                            className="text-button"
                            onClick={() => navigate("personalize")}
                          >
                            Fine-tune your taste <Icon name="arrow" size={16} />
                          </button>
                        </>
                      ) : (
                        <p>Choose a movie to see what connects it to you.</p>
                      )}
                      <div className="transparency">
                        <Icon name="info" size={15} />
                        <p>
                          Artwork sets the mood; it isn’t an official movie
                          poster.
                        </p>
                      </div>
                    </aside>
                  </div>
                  <div className="stat-strip">
                    <Stat
                      label="MOVIES TO DISCOVER"
                      value={format(catalog.movies.length)}
                      sub="Across the MovieLens catalog"
                    />
                    <Stat
                      label="COMMUNITY RATINGS"
                      value={format(catalog.rating_count)}
                      sub="Real, anonymized rating data"
                    />
                    <Stat
                      label="YOUR TASTE SIGNALS"
                      value={format(
                        Object.keys(preferences.ratings).length +
                          preferences.saved.length +
                          preferences.liked.length,
                      )}
                      sub="Ratings, likes, and saves"
                    />
                    <Stat
                      label="OFFLINE PRECISION @ 10"
                      value={percent(
                        catalog.evaluation.results.hybrid.precision_at_10,
                      )}
                      sub={`${catalog.evaluation.eligible_users} eligible test profiles`}
                    />
                  </div>
                </>
              )}
              {page === "personalize" && (
                <div className="settings-layout">
                  <section className="surface">
                    <div className="section-heading">
                      <span className="icon-bubble">
                        <Icon name="sliders" />
                      </span>
                      <div>
                        <h2>What draws you in?</h2>
                        <p>
                          Pick a few genres. Your feed updates as your taste
                          evolves.
                        </p>
                      </div>
                    </div>
                    <div className="genre-picker">
                      {genres.map((g) => (
                        <button
                          disabled={busy}
                          key={g}
                          aria-pressed={preferences.genres.includes(g)}
                          className={
                            preferences.genres.includes(g) ? "chosen" : ""
                          }
                          onClick={() =>
                            update(
                              {
                                ...preferences,
                                genres: preferences.genres.includes(g)
                                  ? preferences.genres.filter((x) => x !== g)
                                  : [...preferences.genres, g],
                              },
                              "Your genre preferences are updated.",
                            )
                          }
                        >
                          {g}
                          {preferences.genres.includes(g) && (
                            <Icon name="check" size={15} />
                          )}
                        </button>
                      ))}
                    </div>
                    <div className="panel-divider" />
                    <h2>Your ratings</h2>
                    <p className="muted">
                      The demo starts with five example ratings. Edit them, or
                      start fresh.
                    </p>
                    <div className="rating-history">
                      {Object.entries(preferences.ratings).map(
                        ([id, rating]) => {
                          const m = catalog.movies.find(
                            (m) => m.id === Number(id),
                          );
                          return (
                            m && (
                              <div key={id}>
                                <span>
                                  {title(m)}
                                  <small>{year(m)}</small>
                                </span>
                                <select
                                  disabled={busy}
                                  aria-label={`Rate ${title(m)}`}
                                  value={rating}
                                  onChange={(e) => rate(m.id, e.target.value)}
                                >
                                  {ratingOptions.map((r) => (
                                    <option key={r}>{r}</option>
                                  ))}
                                </select>
                                <button
                                  disabled={busy}
                                  aria-label={`Remove rating for ${title(m)}`}
                                  onClick={() => rate(m.id, "")}
                                >
                                  <Icon name="close" size={16} />
                                </button>
                              </div>
                            )
                          );
                        },
                      )}
                      {!Object.keys(preferences.ratings).length && (
                        <p>
                          No ratings yet. Explore the catalog to add your first.
                        </p>
                      )}
                    </div>
                  </section>
                  <aside className="surface settings-aside">
                    <span className="icon-bubble">
                      <Icon name="user" />
                    </span>
                    <h2>Your space to explore</h2>
                    <p>
                      {portable
                        ? "Your preferences stay in this browser. There’s no account to create, and no one else changes your feed."
                        : "Your isolated demo profile persists in PostgreSQL for seven days."}
                    </p>
                    <button
                      disabled={busy}
                      className="secondary"
                      onClick={() =>
                        update(
                          initialPreferences(),
                          "Example profile restored.",
                        )
                      }
                    >
                      <Icon name="reset" size={16} />
                      Restore example taste
                    </button>
                    <button
                      disabled={busy}
                      className="text-button"
                      onClick={() =>
                        update(
                          emptyPreferences(),
                          "Fresh start. Pick a genre or rate a movie.",
                        )
                      }
                    >
                      Start with a blank profile
                    </button>
                    <p className="context-note">
                      Resets only your demo preferences.
                    </p>
                  </aside>
                </div>
              )}
              {page === "analytics" && (
                <>
                  <div className="stat-strip analytics-stats">
                    <Stat
                      label="CATALOG"
                      value={format(catalog.movies.length)}
                      sub="Movies with genre metadata"
                    />
                    <Stat
                      label="RATINGS"
                      value={format(catalog.rating_count)}
                      sub={`${format(catalog.user_count)} dataset profiles`}
                    />
                    <Stat
                      label="YOUR RATINGS"
                      value={String(Object.keys(preferences.ratings).length)}
                      sub="Includes retained example ratings"
                    />
                    <Stat
                      label="YOUR SAVED MOVIES"
                      value={String(preferences.saved.length)}
                      sub="Ready for movie night"
                    />
                  </div>
                  <div className="analytics-grid">
                    <section className="surface">
                      <h2>A world of genres</h2>
                      <p className="muted">
                        Movie counts; each movie can belong to multiple genres.
                      </p>
                      <div className="genre-chart">
                        {genres
                          .map(
                            (g) =>
                              [
                                g,
                                catalog.movies.filter((m) =>
                                  m.genres.includes(g),
                                ).length,
                              ] as const,
                          )
                          .sort((a, b) => b[1] - a[1])
                          .slice(0, 9)
                          .map(([g, n]) => (
                            <div key={g}>
                              <span>{g}</span>
                              <div>
                                <i
                                  style={{
                                    width: `${(n / catalog.movies.length) * 100}%`,
                                  }}
                                />
                              </div>
                              <b>{format(n)}</b>
                            </div>
                          ))}
                      </div>
                    </section>
                    <section className="surface">
                      <h2>Measured, not assumed.</h2>
                      <p className="muted">
                        Offline evaluation against a popularity baseline.
                      </p>
                      <div className="table-scroll">
                        <table>
                          <thead>
                            <tr>
                              <th>Metric</th>
                              <th>SignalRank</th>
                              <th>Popularity</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(
                              [
                                ["Precision @ 10", "precision_at_10"],
                                ["Recall @ 10", "recall_at_10"],
                                ["Catalog coverage", "catalog_coverage"],
                              ] as const
                            ).map(([label, key]) => (
                              <tr key={key}>
                                <th>{label}</th>
                                <td>
                                  {percent(
                                    catalog.evaluation.results.hybrid[key],
                                  )}
                                </td>
                                <td>
                                  {percent(
                                    catalog.evaluation.results.popularity[key],
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <p className="method-note">
                        Global time split:{" "}
                        {format(catalog.evaluation.train_ratings)} training
                        ratings and {format(catalog.evaluation.test_ratings)}{" "}
                        held-out ratings. {catalog.evaluation.eligible_users}{" "}
                        eligible profiles;{" "}
                        {catalog.evaluation.excluded_test_users} excluded for
                        insufficient history or relevant test items.
                      </p>
                      <p className="method-note">
                        Precision: relevant hits among ten picks. Recall: share
                        of held-out favorites found. Coverage: share of the
                        training catalog recommended. These are offline results,
                        not live engagement.
                      </p>
                      <button
                        className="text-button"
                        onClick={() => navigate("model")}
                      >
                        See how it works <Icon name="arrow" size={16} />
                      </button>
                    </section>
                  </div>
                </>
              )}
              {page === "model" && (
                <div className="model-layout">
                  <section className="surface">
                    <h2>Three signals. One thoughtful feed.</h2>
                    <p className="muted">
                      An explainable recommendation system built with
                      scikit-learn.
                    </p>
                    {[
                      [
                        "01",
                        "Shared viewing patterns",
                        "Movies connect through positive ratings from the same MovieLens viewers. Cosine nearest neighbors finds related item profiles. Similarity contributes up to 60% of the ranking formula.",
                      ],
                      [
                        "02",
                        "Your kind of story",
                        "Genres you choose and movies you rate, like, or save shape your preferences. Genre affinity contributes up to 25%; low ratings can reduce it.",
                      ],
                      [
                        "03",
                        "Community perspective",
                        "A smoothed community rating contributes up to 15%. New profiles get useful picks without treating a single five-star rating as a consensus.",
                      ],
                    ].map(([n, h, p]) => (
                      <div className="model-step" key={n}>
                        <span>{n}</span>
                        <div>
                          <h3>{h}</h3>
                          <p>{p}</p>
                        </div>
                      </div>
                    ))}
                    <div className="callout">
                      <Icon name="info" />
                      <p>
                        Rated movies leave your For You feed. Likes and saves
                        are weaker signals than high ratings. These weights are
                        design choices, not measured causal importance or
                        confidence.
                      </p>
                    </div>
                  </section>
                  <aside className="surface">
                    <h2>Under the surface</h2>
                    <dl className="specs">
                      <dt>Dataset</dt>
                      <dd>MovieLens latest-small</dd>
                      <dt>Training</dt>
                      <dd>Python · scikit-learn</dd>
                      <dt>Retrieval</dt>
                      <dd>Sparse cosine item neighbors</dd>
                      <dt>Model built</dt>
                      <dd>{new Date(catalog.built_at).toLocaleDateString()}</dd>
                      <dt>This demo</dt>
                      <dd>
                        {portable
                          ? "Browser ranking · local preferences"
                          : "FastAPI · PostgreSQL sessions"}
                      </dd>
                    </dl>
                    <h3>Honest limitations</h3>
                    <p className="method-note">
                      The catalog ends in 2018. Historical ratings reflect
                      selection and popularity biases. Offline scores don’t
                      predict engagement. Saves indicate interest, not
                      necessarily enjoyment. Genre artwork is illustrative.
                    </p>
                    <a
                      className="text-button"
                      href="https://grouplens.org/datasets/movielens/latest/"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Dataset and attribution <Icon name="arrow" size={16} />
                    </a>
                    <details>
                      <summary>Dataset fingerprint</summary>
                      <code className="fingerprint">{catalog.sha256}</code>
                    </details>
                  </aside>
                </div>
              )}
              <footer>
                <span>
                  SignalRank <i>·</i> Find something that stays with you.
                </span>
                <span>
                  MovieLens data <i>·</i> Photography from Unsplash
                </span>
              </footer>
            </>
          )}
        </main>
      </div>
      {notice && (
        <div className="toast" role="status">
          <Icon name="info" size={18} />
          {notice}
          <button aria-label="Dismiss message" onClick={() => setNotice("")}>
            <Icon name="close" size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
function Stat({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{sub}</small>
    </div>
  );
}
function Explanation({ movie, ranked }: { movie: Movie; ranked?: Ranked }) {
  const signals = ranked?.signals || {
    similarity: 0,
    genres: 0,
    community: 0.15 * movie.quality,
  };
  return (
    <>
      <div className="reason">
        <span className="icon-bubble">
          <Icon name="user" />
        </span>
        <div>
          <h4>Connected to your taste</h4>
          <p>
            {ranked?.explanation || "Rate this movie to shape future picks."}
          </p>
        </div>
      </div>
      <div className="reason">
        <span className="icon-bubble">
          <Icon name="chart" />
        </span>
        <div>
          <h4>A community perspective</h4>
          <p>
            {movie.mean
              ? `${movie.mean.toFixed(1)} out of 5 from ${format(movie.count)} ratings.`
              : "No ratings yet."}
          </p>
        </div>
      </div>
      <div className="signal-breakdown">
        <span>RANKING CONTRIBUTIONS</span>
        {(
          [
            ["Viewing patterns", signals.similarity],
            ["Genre affinity", signals.genres],
            ["Community", signals.community],
          ] as const
        ).map(([name, value]) => (
          <div key={name}>
            <label>
              {name}
              <small>{value.toFixed(3)}</small>
            </label>
            <div className="bar">
              <i style={{ width: `${(Math.max(0, value) / 0.6) * 100}%` }} />
            </div>
          </div>
        ))}
        <p>Weighted scores, not confidence percentages.</p>
      </div>
    </>
  );
}
