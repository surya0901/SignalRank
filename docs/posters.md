# Film poster matching

3,866 of 9,742 catalog films have poster references. No image is selected from a genre.
Both input datasets are joined to MovieLens `links.csv` through numeric IMDb IDs, never
through the row position or an assumed equivalence of MovieLens edition identifiers.

Sources:
- https://huggingface.co/datasets/pinecone/movie-posters (Parquet metadata)
- https://github.com/vectorsss/movielens_100k_1m_extension (ml-1m links_artificial.csv and movie_posters.csv)
- https://en.wikipedia.org/wiki/Star_Wars_(film) (replacement for a broken Star Wars poster URL)

To regenerate, install pyarrow in a development environment and run:

```sh
python scripts/import-posters.py MOVIELENS_ZIP POSTERS_PARQUET CLASSIC_LINKS_CSV CLASSIC_POSTERS_CSV
```

The Star Wars override is a reviewed reference in `frontend/src/posters.json`. Preserve
that entry when refreshing metadata. Image URLs are loaded from their original hosts;
no poster image files are redistributed in the repository. Rights remain with their owners.
Third-party metadata may have errors. Missing references or failed image loads render a
labeled title card. Representative poster endpoints were checked during this release;
this is not a claim that every external URL is permanently available.
