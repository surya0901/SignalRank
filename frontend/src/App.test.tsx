import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { loadData, persist } from "./data";
import { Catalog, emptyPreferences } from "./engine";

vi.mock("./data", () => ({
  loadData: vi.fn(),
  persist: vi.fn(),
  portable: true,
}));
const catalog: Catalog = {
  movies: [
    {
      id: 1,
      title: "Example Movie (2000)",
      genres: ["Drama"],
      mean: 4,
      count: 10,
      quality: 0.8,
      neighbors: [[2, 0.9]],
    },
    {
      id: 2,
      title: "Another Movie (2001)",
      genres: ["Comedy"],
      mean: 3,
      count: 5,
      quality: 0.6,
      neighbors: [[1, 0.9]],
    },
  ],
  rating_count: 15,
  user_count: 3,
  sha256: "fixture",
  built_at: "2026-09-13T00:00:00Z",
  method: "test",
  evaluation: {
    protocol: "fixture",
    train_ratings: 12,
    test_ratings: 3,
    eligible_users: 2,
    excluded_test_users: 0,
    candidate_movies: 2,
    k: 10,
    scope: "test",
    results: {
      hybrid: {
        precision_at_10: 0.1,
        recall_at_10: 0.2,
        catalog_coverage: 0.5,
      },
      popularity: {
        precision_at_10: 0,
        recall_at_10: 0,
        catalog_coverage: 0.5,
      },
    },
  },
};
beforeEach(() => {
  vi.mocked(loadData).mockResolvedValue([catalog, emptyPreferences()]);
  vi.mocked(persist).mockResolvedValue(undefined);
});
describe("interactive discovery", () => {
  it("searches the actual catalog", async () => {
    render(<App />);
    await screen.findByLabelText("Save Example Movie");
    fireEvent.change(screen.getByLabelText("Search movies"), {
      target: { value: "Another" },
    });
    expect(
      screen.queryByLabelText("Save Example Movie"),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText("Save Another Movie")).toBeInTheDocument();
  });
  it("saves a movie and displays it in the collection", async () => {
    render(<App />);
    fireEvent.click(await screen.findByLabelText("Save Example Movie"));
    await waitFor(() =>
      expect(persist).toHaveBeenCalledWith(
        expect.objectContaining({ saved: [1] }),
      ),
    );
    await waitFor(() =>
      expect(screen.getByLabelText("Save Example Movie")).toHaveAttribute(
        "aria-pressed",
        "true",
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Saved 1" }));
    expect(screen.getByLabelText("Save Example Movie")).toBeInTheDocument();
    expect(
      screen.queryByLabelText("Save Another Movie"),
    ).not.toBeInTheDocument();
  });
  it("removes rated movies from For You", async () => {
    render(<App />);
    fireEvent.change(await screen.findByLabelText("Rate Example Movie"), {
      target: { value: "4.5" },
    });
    await waitFor(() =>
      expect(
        screen.queryByLabelText("Rate Example Movie"),
      ).not.toBeInTheDocument(),
    );
  });
  it("can retry after loading fails", async () => {
    vi.mocked(loadData).mockRejectedValueOnce(new Error("offline"));
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
    expect(
      await screen.findByLabelText("Save Example Movie"),
    ).toBeInTheDocument();
  });
});
