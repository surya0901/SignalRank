export type Preferences = {
  ratings: Record<string, number>;
  saved: number[];
  liked: number[];
  genres: string[];
};
export type Movie = {
  id: number;
  title: string;
  genres: string[];
  mean: number | null;
  count: number;
  quality: number;
  neighbors: [number, number][];
};
export type Ranked = Movie & {
  score: number;
  signals: { similarity: number; genres: number; community: number };
  explanation: string;
};
export type Metric = {
  precision_at_10: number | null;
  recall_at_10: number | null;
  catalog_coverage: number;
};
export type Catalog = {
  movies: Movie[];
  rating_count: number;
  user_count: number;
  sha256: string;
  built_at: string;
  method: string;
  evaluation: {
    protocol: string;
    train_ratings: number;
    test_ratings: number;
    eligible_users: number;
    excluded_test_users: number;
    candidate_movies: number;
    k: number;
    scope: string;
    results: { hybrid: Metric; popularity: Metric };
  };
};
export const initialPreferences = (): Preferences => ({
  ratings: { "1": 4.5, "260": 5, "2571": 4.5, "2959": 4, "4993": 5 },
  saved: [],
  liked: [],
  genres: ["Sci-Fi", "Adventure"],
});
export const emptyPreferences = (): Preferences => ({
  ratings: {},
  saved: [],
  liked: [],
  genres: [],
});
const rounded = (n: number) => Math.round(n * 1e6) / 1e6;
export function rank(catalog: Catalog, state: Preferences): Ranked[] {
  const affinity: Record<string, number> = {},
    collaborative: Record<number, number> = {},
    references: Record<number, [number, string]> = {};
  for (const genre of state.genres)
    affinity[genre] = (affinity[genre] || 0) + 2;
  for (const movie of catalog.movies) {
    const rating = state.ratings[movie.id];
    const weight =
      (rating === undefined ? 0 : (rating - 3) / 2) +
      0.6 * Number(state.liked.includes(movie.id)) +
      0.35 * Number(state.saved.includes(movie.id));
    if (!weight) continue;
    for (const genre of movie.genres)
      affinity[genre] = (affinity[genre] || 0) + weight;
    if (weight > 0)
      for (const [id, similarity] of movie.neighbors) {
        const value = weight * similarity;
        collaborative[id] = (collaborative[id] || 0) + value;
        if (value > (references[id]?.[0] || 0))
          references[id] = [value, movie.title];
      }
  }
  const maxCollab = Math.max(0, ...Object.values(collaborative)) || 1;
  const maxGenre = Math.max(0, ...Object.values(affinity).map(Math.abs)) || 1;
  return catalog.movies
    .filter((m) => state.ratings[m.id] === undefined)
    .map((movie) => {
      const genreScore =
        movie.genres.reduce((sum, g) => sum + (affinity[g] || 0), 0) /
        (Math.max(1, movie.genres.length) * maxGenre);
      const signals = {
        similarity: rounded((0.6 * (collaborative[movie.id] || 0)) / maxCollab),
        genres: rounded(0.25 * Math.max(-1, genreScore)),
        community: rounded(0.15 * movie.quality),
      };
      let explanation = `Community pick from ${movie.count.toLocaleString()} MovieLens ratings`;
      if (signals.similarity > 0)
        explanation = `Similar viewing patterns to ${references[movie.id][1]}`;
      else if (genreScore > 0)
        explanation = `Matches your interest in ${movie.genres
          .filter((g) => (affinity[g] || 0) > 0)
          .slice(0, 2)
          .join(", ")}`;
      return {
        ...movie,
        signals,
        score: rounded(signals.similarity + signals.genres + signals.community),
        explanation,
      };
    })
    .sort((a, b) => b.score - a.score || b.count - a.count || a.id - b.id);
}
export const year = (movie: Movie) =>
  movie.title.match(/\((\d{4})\)\s*$/)?.[1] || "—";
export const title = (movie: Movie) =>
  movie.title.replace(/\s*\(\d{4}\)\s*$/, "");
