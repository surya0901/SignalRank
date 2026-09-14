import { render, screen, fireEvent } from "@testing-library/react";
import { expect, it } from "vitest";
import MoviePoster from "./MoviePoster";
import type { Movie } from "./engine";
const movie: Movie = { id: 318, title: "Shawshank Redemption, The (1994)", genres: ["Drama"], mean: 4, count: 10, quality: 0.8, neighbors: [] };
it("uses the film poster and falls back after a failed image request", () => {
  render(<MoviePoster movie={movie} />);
  const image = screen.getByRole("img", { name: /Shawshank.*poster/ });
  expect(image.getAttribute("src")).toContain("m.media-amazon.com");
  fireEvent.error(image);
  expect(screen.getByText("Poster unavailable")).toBeInTheDocument();
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
});
it("shows a labeled title card when there is no verified poster", () => {
  render(<MoviePoster movie={{...movie, id: -1}} />);
  expect(screen.getByText("Poster unavailable")).toBeInTheDocument();
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
});
