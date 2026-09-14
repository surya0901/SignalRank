import { Catalog, Preferences, initialPreferences } from "./engine";
export const portable = import.meta.env.VITE_PORTABLE_DEMO === "true";
const key = "signalrank.preferences.v1";
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...options,
    credentials: "same-origin",
  });
  if (!response.ok)
    throw new Error(
      response.status === 401
        ? "Your demo session expired. Reload to start again."
        : "Unable to save right now. Please try again.",
    );
  return response.json();
}
function readPreferences(): Preferences {
  try {
    const raw = JSON.parse(localStorage.getItem(key) || "null");
    if (
      raw &&
      raw.ratings &&
      !Array.isArray(raw.ratings) &&
      Array.isArray(raw.saved) &&
      Array.isArray(raw.liked) &&
      Array.isArray(raw.genres)
    ) {
      return {
        ratings: Object.fromEntries(
          Object.entries(raw.ratings)
            .filter(
              ([id, r]) =>
                /^\d+$/.test(id) &&
                typeof r === "number" &&
                r >= 0.5 &&
                r <= 5 &&
                r * 2 === Math.trunc(r * 2),
            )
            .map(([id, r]) => [id, Number(r)]),
        ),
        saved: raw.saved.filter(Number.isInteger),
        liked: raw.liked.filter(Number.isInteger),
        genres: raw.genres.filter((g: unknown) => typeof g === "string"),
      };
    }
  } catch {
    /* Storage may be unavailable. Start an isolated example profile. */
  }
  return initialPreferences();
}
export async function loadData(): Promise<[Catalog, Preferences]> {
  return Promise.all([
    request<Catalog>(portable ? `${import.meta.env.BASE_URL}data/catalog.json` : "/api/catalog"),
    portable
      ? Promise.resolve(readPreferences())
      : request<Preferences>("/api/auth/demo", { method: "POST" }),
  ]);
}
export async function persist(state: Preferences): Promise<void> {
  if (portable) {
    localStorage.setItem(key, JSON.stringify(state));
    return;
  }
  await request("/api/me", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state),
  });
}
