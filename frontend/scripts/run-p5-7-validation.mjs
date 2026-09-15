import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import process from "node:process";

const root = resolve(import.meta.dirname, "..");
const node = process.execPath;
const commands = [
  ["generate", resolve(root, "scripts", "generate-p5-7-cases.mjs"), []],
  ["workspace", resolve(root, "scripts", "verify-workspace.mjs"), []],
  ["repeatability", resolve(root, "scripts", "verify-p5-7-repeatability.mjs"), []],
  [
    "lint",
    resolve(root, "node_modules", "eslint", "bin", "eslint.js"),
    [".", "--max-warnings", "0"],
  ],
  ["typecheck", resolve(root, "scripts", "run-workspace.mjs"), ["typecheck"]],
  [
    "unit",
    resolve(root, "node_modules", "vitest", "vitest.mjs"),
    ["--config", "vitest.workspace.ts", "run", "--coverage"],
  ],
  ["build", resolve(root, "scripts", "run-workspace.mjs"), ["build"]],
  ["bundles", resolve(root, "scripts", "verify-bundles.mjs"), []],
];
const completed = [];
for (const [name, script, args] of commands) {
  const result = spawnSync(node, [script, ...args], {
    cwd: root,
    env: { ...process.env, PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD: "1" },
    stdio: "inherit",
    timeout: 600_000,
    windowsHide: true,
  });
  if (result.error || result.status !== 0) {
    process.stderr.write(`p5_7_validation_failed:${name}\n`);
    process.exit(result.status ?? 1);
  }
  completed.push(name);
}
process.stdout.write(`${JSON.stringify({ status: "pass", completed })}\n`);
