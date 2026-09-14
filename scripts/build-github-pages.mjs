import { spawnSync } from "node:child_process";
import { writeFileSync } from "node:fs";
const result = spawnSync("npm", ["run", "build"], { stdio: "inherit", env: { ...process.env, VITE_BASE_PATH: "/SignalRank/" } });
if (result.status !== 0) process.exit(result.status || 1);
writeFileSync("dist/.nojekyll", "");
