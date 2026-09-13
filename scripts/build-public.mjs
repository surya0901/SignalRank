import { spawnSync } from "node:child_process";
const build = spawnSync("npm", ["--prefix", "frontend", "run", "build"], {
  stdio: "inherit",
  env: { ...process.env, VITE_PORTABLE_DEMO: "true" },
});
if (build.status !== 0) process.exit(build.status ?? 1);
await import("./stage-site.mjs");
