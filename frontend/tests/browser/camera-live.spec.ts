import { expect, test, type Page } from "@playwright/test";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { basename, join, resolve } from "node:path";

const dist = resolve("apps/operations-center/dist/assets");
const media = resolve("..", "output", "p5-3", "generated-media");

async function mountOperations(page: Page, route = "/operations") {
  await page.route(/^http:\/\/127\.0\.0\.1:4173\/operations(?:\/.*)?$/u, async (request) => {
    if (request.request().resourceType() === "document")
      await request.fulfill({
        status: 200,
        contentType: "text/html",
        body: '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><base href="/assets/"></head><body><div id="root"></div></body></html>',
      });
    else await request.continue();
  });
  await page.route("**/assets/**", async (request) => {
    const file = join(dist, basename(new URL(request.request().url()).pathname));
    if (existsSync(file))
      await request.fulfill({ path: file, contentType: "application/javascript" });
    else await request.continue();
  });
  await page.route("**/media-edge/sessions/**", async (request) => {
    const url = new URL(request.request().url());
    const match = /SYN-SESSION-(\d{4})\/(master\.m3u8|segment-\d+\.ts)$/u.exec(url.pathname);
    const authorized = request.request().headers().authorization?.startsWith("HCAM-Grant g1_");
    if (!match || !authorized) return request.fulfill({ status: 403, body: "denied" });
    const streamNumber = match[1]!;
    const resource = match[2]!;
    const file = join(media, `stream-${streamNumber}`, "low", resource);
    return request.fulfill({
      path: file,
      contentType: resource.endsWith(".m3u8") ? "application/vnd.apple.mpegurl" : "video/mp2t",
    });
  });
  await page.goto(route);
  for (const css of readdirSync(dist).filter((name) => name.endsWith(".css")))
    await page.addStyleTag({ path: join(dist, css) });
  const main = readdirSync(dist)
    .filter((name) => name.endsWith(".js"))
    .find((name) => readFileSync(join(dist, name), "utf8").includes("Operations Center"));
  if (!main) throw new Error("operations_bundle_not_found");
  await page.addScriptTag({ content: readFileSync(join(dist, main), "utf8"), type: "module" });
}

test("catalogue drills into camera diagnostics", async ({ page }) => {
  await mountOperations(page);
  await expect(page.getByRole("heading", { name: "Camera catalogue" })).toBeVisible();
  await expect(page.getByRole("row")).toHaveCount(11);
  await page.getByRole("link", { name: "Open Generated camera 0001" }).click();
  await expect(page.getByRole("heading", { name: "Stream capability" })).toBeVisible();
  await expect(page.getByText("Metadata probe completed")).toBeVisible();
});

test("live workspace plays admitted generated HLS", async ({ page }, testInfo) => {
  await mountOperations(page, "/operations/live");
  await expect(page.getByRole("heading", { name: "Live monitoring workspace" })).toBeVisible();
  await expect(page.getByText("4 / 4")).toBeVisible();
  await expect(page.getByText("Generated live session").first()).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: testInfo.outputPath("p5-3-live-workspace.png"), fullPage: true });
  await page.getByRole("button", { name: "Pause Primary generated stream" }).first().click();
  await expect(page.getByText("paused").first()).toBeVisible();
  await page.getByRole("button", { name: "Resume Primary generated stream" }).first().click();
  await expect(page.getByText("Generated live session").first()).toBeVisible();
  await page.getByRole("button", { name: "Release Primary generated stream" }).first().click();
  await expect(page.getByText("released").first()).toBeVisible();
});
