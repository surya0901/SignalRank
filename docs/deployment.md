# Deployment

## GitHub Pages demo

Public address: https://surya0901.github.io/SignalRank/

The demo is published from the `gh-pages` branch, root directory. Build with:

```sh
npm --prefix frontend ci
npm run build:github-pages
```

Publish the contents of `dist/` to `gh-pages`, including `.nojekyll`. GitHub Pages builds
that branch automatically. `VITE_BASE_PATH=/SignalRank/` is applied by the build script;
catalog, poster fallback, favicon and JavaScript paths support the repository subdirectory.
Source changes alone do not update the published branch; rebuild and publish `dist/`.

The public demo runs the trained ranking model in the browser and keeps each visitor's
preferences in local storage. No Python API or PostgreSQL is hosted on GitHub Pages.
The full-stack application remains available and tested locally through Docker Compose.

This release replaces the previous hosting address. GitHub Pages publication verification
is recorded in `testing.md` after the service reports success.
