import { expect, test } from "@playwright/test";
test("review surface discloses authoritative concurrency and no retry", async ({ page }) => {
  await page.goto("http://127.0.0.1:4175/intelligence/alerts/SYN-ALERT-0001");
  await expect(page.getByText('"SYN-ETAG-1"')).toBeVisible();
  await expect(page.getByText("disabled")).toBeVisible();
  await page.goto("http://127.0.0.1:4175/intelligence/review");
  await expect(page.getByText("Client override")).toBeVisible();
  await expect(page.getByText("denied")).toBeVisible();
  await page.getByRole("button", { name: "Review generated proposal" }).click();
  await expect(page.getByText("ETag + revision + idempotency")).toBeVisible();
});
