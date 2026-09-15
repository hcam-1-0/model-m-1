import { expect, test } from "@playwright/test";
import process from "node:process";
test("P5.6 portal exposes no effective, secret, external, or raw-data path", async ({ page }) => {
  const target = process.env.HCAM_P56_TARGET ?? "operations";
  const url =
    target === "admin"
      ? "http://127.0.0.1:4178/admin"
      : target === "security"
        ? "http://127.0.0.1:4179/security"
        : "http://127.0.0.1:4180/operations/platform";
  await page.goto(url);
  await expect(page.locator("video, audio, img[src], a[download]")).toHaveCount(0);
  const body = await page.locator("body").innerText();
  expect(body).not.toMatch(/rtsp:\/\/|whep:\/\/|BEGIN PRIVATE KEY|Bearer\s+[A-Za-z0-9._-]+/i);
  expect(
    await page.evaluate(() =>
      performance
        .getEntriesByType("resource")
        .every((entry) => new URL(entry.name).hostname === "127.0.0.1"),
    ),
  ).toBe(true);
});
