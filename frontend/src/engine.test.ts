import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { Catalog, Preferences, rank } from "./engine";
const catalog: Catalog = JSON.parse(
  readFileSync("public/data/catalog.json", "utf8"),
);
const cases: { state: Preferences; ids: number[] }[] = JSON.parse(
  readFileSync("../docs/ranking-parity.json", "utf8"),
);
describe("Python and browser ranking parity", () => {
  cases.forEach((sample, i) =>
    it(`matches Python top 24 for profile ${i + 1}`, () => {
      expect(
        rank(catalog, sample.state)
          .slice(0, 24)
          .map((m) => m.id),
      ).toEqual(sample.ids);
    }),
  );
  it("has no self-neighbors and finite scores", () => {
    expect(
      catalog.movies.every((m) =>
        m.neighbors.every(([id, s]) => id !== m.id && s > 0 && s <= 1),
      ),
    ).toBe(true);
    expect(
      rank(catalog, cases[0].state).every((m) => Number.isFinite(m.score)),
    ).toBe(true);
  });
});
