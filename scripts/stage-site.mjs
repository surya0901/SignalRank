import { cpSync, mkdirSync } from "node:fs";
mkdirSync("dist", { recursive: true });
cpSync("frontend/dist", "dist", { recursive: true });
