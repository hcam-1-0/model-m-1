import { defineConfig, devices } from "@playwright/test";
import process from "node:process";

const node = `"${process.execPath}"`;
const p55Target = process.env.HCAM_P55_TARGET;
const p55Investigation = p55Target === "investigation";
const p55Evidence = p55Target === "evidence";
const p56Target = process.env.HCAM_P56_TARGET;
const p56Admin = p56Target === "admin";
const p56Security = p56Target === "security";
const p56Operations = p56Target === "operations";
const p57Target = process.env.HCAM_P57_TARGET;
const p57Engine = process.env.HCAM_P57_ENGINE ?? "edge";
if (!new Set(["edge", "chromium"]).has(p57Engine)) {
  throw new Error("invalid_P5_7_engine");
}
const p57EngineSuffix = p57Engine === "edge" ? "" : `-${p57Engine}`;

const commandServer = {
  command: `${node} ./node_modules/vite/bin/vite.js --config apps/command-center/vite.config.ts preview --outDir apps/command-center/dist --port 4173`,
  url: "http://127.0.0.1:4173",
  reuseExistingServer: false,
  timeout: 30_000,
};
const gisServer = {
  command: `${node} ./node_modules/vite/bin/vite.js --config apps/gis-center/vite.config.ts preview --outDir apps/gis-center/dist --port 4174`,
  url: "http://127.0.0.1:4174",
  reuseExistingServer: false,
  timeout: 30_000,
};
const intelligenceServer = {
  command: `${node} ./node_modules/vite/bin/vite.js --config apps/intelligence-center/vite.config.ts preview --outDir apps/intelligence-center/dist --port 4175`,
  url: "http://127.0.0.1:4175",
  reuseExistingServer: false,
  timeout: 30_000,
};
const investigationServer = {
  command: `${node} ./node_modules/vite/bin/vite.js --config apps/investigation-center/vite.config.ts preview --outDir apps/investigation-center/dist --port 4176`,
  url: "http://127.0.0.1:4176",
  reuseExistingServer: false,
  timeout: 30_000,
};
const evidenceServer = {
  command: `${node} ./node_modules/vite/bin/vite.js --config apps/evidence-center/vite.config.ts preview --outDir apps/evidence-center/dist --port 4177`,
  url: "http://127.0.0.1:4177",
  reuseExistingServer: false,
  timeout: 30_000,
};
const adminServer = {
  command: `${node} ./node_modules/vite/bin/vite.js --config apps/admin-center/vite.config.ts preview --outDir apps/admin-center/dist --port 4178 --strictPort`,
  url: "http://127.0.0.1:4178",
  reuseExistingServer: false,
  timeout: 30_000,
};
const securityServer = {
  command: `${node} ./node_modules/vite/bin/vite.js --config apps/security-center/vite.config.ts preview --outDir apps/security-center/dist --port 4179 --strictPort`,
  url: "http://127.0.0.1:4179",
  reuseExistingServer: false,
  timeout: 30_000,
};
const operationsServer = {
  command: `${node} ./node_modules/vite/bin/vite.js --config apps/operations-center/vite.config.ts preview --outDir apps/operations-center/dist --port 4180 --strictPort`,
  url: "http://127.0.0.1:4180",
  reuseExistingServer: false,
  timeout: 30_000,
};
const phase57Servers = {
  command: commandServer,
  gis: gisServer,
  operations: operationsServer,
  intelligence: intelligenceServer,
  investigation: investigationServer,
  evidence: evidenceServer,
  admin: adminServer,
  security: securityServer,
} as const;
const phase57Server = p57Target
  ? phase57Servers[p57Target as keyof typeof phase57Servers]
  : undefined;
if (p57Target && !phase57Server) throw new Error("invalid_P5_7_target");
const phase56Projects = [
  {
    name: "compact-mobile-390x844",
    use: { ...devices["Pixel 7"], viewport: { width: 390, height: 844 } },
  },
  { name: "tablet-768x1024", use: { viewport: { width: 768, height: 1024 } } },
  { name: "compact-desktop-1280x720", use: { viewport: { width: 1280, height: 720 } } },
  { name: "desktop-1440x900", use: { viewport: { width: 1440, height: 900 } } },
  { name: "full-hd-1920x1080", use: { viewport: { width: 1920, height: 1080 } } },
  { name: "control-room-2560x1440", use: { viewport: { width: 2560, height: 1440 } } },
];
const phase57Projects = [
  { name: "V01-390x844", use: { ...devices["Pixel 7"], viewport: { width: 390, height: 844 } } },
  { name: "V02-768x1024", use: { viewport: { width: 768, height: 1024 } } },
  { name: "V03-1280x720", use: { viewport: { width: 1280, height: 720 } } },
  { name: "V04-1440x900", use: { viewport: { width: 1440, height: 900 } } },
  { name: "V05-1920x1080", use: { viewport: { width: 1920, height: 1080 } } },
  { name: "V06-2560x1440", use: { viewport: { width: 2560, height: 1440 } } },
  { name: "V07-3840x1080", use: { viewport: { width: 3840, height: 1080 } } },
];

export default defineConfig({
  testDir: "./tests/browser",
  outputDir: p57Target
    ? `test-results/artifacts-p57-${p57Target}${p57EngineSuffix}`
    : p55Target
      ? `test-results/artifacts-p55-${p55Target}`
      : p56Target
        ? `test-results/artifacts-p56-${p56Target}`
        : "test-results/artifacts-default",
  ...(p55Investigation
    ? { testMatch: ["investigation-center*.spec.ts"] }
    : p55Evidence
      ? { testMatch: ["evidence-center*.spec.ts", "investigation-evidence-security.spec.ts"] }
      : p56Admin
        ? {
            testMatch: ["admin-center*.spec.ts", "admin-security-operations-security.spec.ts"],
          }
        : p56Security
          ? {
              testMatch: ["security-center*.spec.ts", "admin-security-operations-security.spec.ts"],
            }
          : p56Operations
            ? {
                testMatch: [
                  "platform-operations*.spec.ts",
                  "admin-security-operations-security.spec.ts",
                  "p5-6-c1-c10-c50.spec.ts",
                ],
              }
            : {
                testIgnore: [
                  "admin-center*.spec.ts",
                  "security-center*.spec.ts",
                  "platform-operations*.spec.ts",
                  "admin-security-operations-security.spec.ts",
                  "p5-6-c1-c10-c50.spec.ts",
                ],
              }),
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: [
    ["list"],
    [
      "json",
      {
        outputFile: p57Target
          ? `test-results/browser-results-p57-${p57Target}${p57EngineSuffix}.json`
          : p55Target
            ? `test-results/browser-results-p55-${p55Target}.json`
            : p56Target
              ? `test-results/browser-results-p56-${p56Target}.json`
              : "test-results/browser-results.json",
      },
    ],
  ],
  use: {
    baseURL: phase57Server?.url ?? "http://127.0.0.1:4173",
    browserName: "chromium",
    ...(p57Engine === "edge" ? { channel: "msedge" } : {}),
    serviceWorkers: "block",
    trace: "retain-on-failure",
    video: "off",
    screenshot: "only-on-failure",
  },
  projects: p57Target
    ? phase57Projects
    : p56Target
      ? phase56Projects
      : [
          { name: "desktop", use: { ...devices["Desktop Edge"] } },
          { name: "mobile", use: { ...devices["Pixel 7"] } },
        ],
  webServer: phase57Server
    ? [phase57Server]
    : p55Investigation
      ? [investigationServer]
      : p55Evidence
        ? [evidenceServer]
        : p56Admin
          ? [adminServer]
          : p56Security
            ? [securityServer]
            : p56Operations
              ? [operationsServer]
              : [commandServer, gisServer, intelligenceServer, investigationServer, evidenceServer],
});
