import { readdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import process from "node:process";

const root = resolve(import.meta.dirname, "..");
const node = process.execPath;
const tools = Object.freeze({
  tsc: resolve(root, "node_modules/typescript/bin/tsc"),
  vite: resolve(root, "node_modules/vite/bin/vite.js"),
  eslint: resolve(root, "node_modules/eslint/bin/eslint.js"),
  prettier: resolve(root, "node_modules/prettier/bin/prettier.cjs"),
  vitest: resolve(root, "node_modules/vitest/vitest.mjs"),
  storybook: resolve(root, "node_modules/storybook/dist/bin/dispatcher.js"),
});
function workspaceDirs(group) {
  return readdirSync(join(root, group), { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => join(root, group, entry.name))
    .filter((path) => {
      try {
        return JSON.parse(readFileSync(join(path, "package.json"), "utf8")).private === true;
      } catch {
        return false;
      }
    })
    .sort();
}
function run(script, args, cwd = root, timeout = 120_000) {
  const result = spawnSync(node, [script, ...args], {
    cwd,
    env: process.env,
    encoding: "utf8",
    timeout,
    stdio: "inherit",
    windowsHide: true,
  });
  if (result.error || result.status !== 0) process.exit(result.status ?? 1);
}
function typecheck() {
  for (const path of [...workspaceDirs("packages"), ...workspaceDirs("apps")])
    run(tools.tsc, ["-p", join(path, "tsconfig.json")]);
  run(tools.tsc, ["-p", join(root, "packages", "ui", ".storybook", "tsconfig.json")]);
  run(tools.tsc, ["-p", join(root, "tests", "tsconfig.json")]);
}
function formatCheck() {
  run(tools.prettier, [
    "--check",
    "apps",
    "packages",
    "scripts",
    "tests",
    "evidence",
    "package.json",
    "pnpm-workspace.yaml",
    "tsconfig.base.json",
    "eslint.config.mjs",
    "prettier.config.mjs",
    "vitest.workspace.ts",
    "playwright.config.ts",
    "dependency-lock-candidate.json",
    "dependency-evidence.json",
  ]);
}
function build(target) {
  const apps = workspaceDirs("apps").filter(
    (path) => !target || path.endsWith(`\\${target}`) || path.endsWith(`/${target}`),
  );
  if (apps.length === 0) throw new Error("unknown_portal_target");
  for (const path of apps)
    run(tools.vite, ["build", "--config", join(path, "vite.config.ts")], path);
}
function validate() {
  run(resolve(root, "scripts/verify-toolchain.mjs"), []);
  run(resolve(root, "scripts/verify-workspace.mjs"), []);
  run(tools.eslint, [".", "--max-warnings", "0"]);
  formatCheck();
  typecheck();
  run(tools.vitest, ["--config", "vitest.workspace.ts", "run", "--coverage"]);
  build();
  run(resolve(root, "scripts/verify-bundles.mjs"), []);
}
const [command, target] = process.argv.slice(2);
if (command === "typecheck") typecheck();
else if (command === "format-check") formatCheck();
else if (command === "build") build(target);
else if (command === "dev") {
  const app = target ?? "command-center";
  const cwd = join(root, "apps", app);
  run(
    tools.vite,
    ["--config", join(cwd, "vite.config.ts"), "--host", "127.0.0.1", "--port", "4173"],
    cwd,
    24 * 60 * 60 * 1000,
  );
} else if (command === "preview") {
  const app = target ?? "command-center";
  const cwd = join(root, "apps", app);
  run(
    tools.vite,
    [
      "preview",
      "--config",
      join(cwd, "vite.config.ts"),
      "--host",
      "127.0.0.1",
      "--port",
      "4173",
      "--strictPort",
    ],
    cwd,
    24 * 60 * 60 * 1000,
  );
} else if (command === "storybook") {
  process.env.STORYBOOK_DISABLE_TELEMETRY = "1";
  run(
    tools.storybook,
    ["build", "-c", "packages/ui/.storybook", "-o", "storybook-static", "--quiet"],
    root,
    300_000,
  );
} else if (command === "validate") validate();
else throw new Error("unsupported_workspace_command");
