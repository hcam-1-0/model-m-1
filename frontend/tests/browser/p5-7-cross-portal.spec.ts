import { expect, test } from "@playwright/test";
import process from "node:process";

test.beforeEach(async ({ page }) => {
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (
      ["http:", "https:"].includes(url.protocol) &&
      !["127.0.0.1", "localhost"].includes(url.hostname)
    ) {
      await route.abort("blockedbyclient");
      return;
    }
    await route.continue();
  });
});

test("authorized portal renders a bounded generated operator surface", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await expect(page.locator("main")).toBeVisible();
  await expect(page.locator("h1:visible").first()).toBeVisible();
  await expect(page.locator("body")).not.toContainText(/operationally active|production ready/iu);
  await page.screenshot({
    path: testInfo.outputPath(
      `${process.env.HCAM_P57_TARGET ?? "unknown"}-${testInfo.project.name}.png`,
    ),
    fullPage: true,
  });
});
