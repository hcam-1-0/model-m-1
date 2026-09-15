import { expect, test, type Page } from "@playwright/test";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { basename, join, resolve } from "node:path";

const dist = resolve("apps/operations-center/dist/assets");
const media = resolve("..", "output", "p5-3", "generated-media");

async function mountLiveWorkspace(page: Page) {
  await page.route(/^http:\/\/127\.0\.0\.1:4173\/operations(?:\/.*)?$/u, async (request) => {
    if (request.request().resourceType() === "document") {
      await request.fulfill({
        status: 200,
        contentType: "text/html",
        body: '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><base href="/assets/"></head><body><div id="root"></div></body></html>',
      });
    } else await request.continue();
  });
  await page.route("**/assets/**", async (request) => {
    const file = join(dist, basename(new URL(request.request().url()).pathname));
    if (existsSync(file))
      await request.fulfill({ path: file, contentType: "application/javascript" });
    else await request.continue();
  });
  await page.route("**/media-edge/sessions/**", async (request) => {
    const match = /SYN-SESSION-(\d{4})\/(master\.m3u8|segment-\d+\.ts)$/u.exec(
      new URL(request.request().url()).pathname,
    );
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
  await page.goto("/operations/live");
  for (const css of readdirSync(dist).filter((name) => name.endsWith(".css")))
    await page.addStyleTag({ path: join(dist, css) });
  const main = readdirSync(dist)
    .filter((name) => name.endsWith(".js"))
    .find((name) => readFileSync(join(dist, name), "utf8").includes("Operations Center"));
  if (!main) throw new Error("operations_bundle_not_found");
  await page.addScriptTag({ content: readFileSync(join(dist, main), "utf8"), type: "module" });
}

test("C1 C4 and C10 generated profiles admit real synthetic HLS sessions", async ({ page }) => {
  await mountLiveWorkspace(page);
  const profile = page.getByLabel("Resource profile");

  await profile.selectOption("low_resource");
  await expect(page.getByText("1 / 1")).toBeVisible();
  await expect(page.getByText("Generated live session")).toHaveCount(1, { timeout: 20_000 });

  await profile.selectOption("enhanced_workstation");
  await expect(page.getByText("4 / 4")).toBeVisible();
  await expect(page.getByText("Generated live session")).toHaveCount(4, { timeout: 20_000 });

  await profile.selectOption("control_room");
  await expect(page.getByText("10 / 10")).toBeVisible();
  await expect(page.getByText("Generated live session")).toHaveCount(10, { timeout: 20_000 });
  await expect(
    page.getByRole("button", { name: /record|snapshot|download|export|print|ptz/i }),
  ).toHaveCount(0);
});
