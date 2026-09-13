import { expect, test } from "@playwright/test";
test("C1 C10 and C50 functional projections remain bounded", async ({ page }) => {
  await page.goto("http://127.0.0.1:4180/operations/platform/capacity");
  await expect(page.getByRole("heading", { name: "Capacity evidence" })).toBeVisible();
  for (const scale of ["C1", "C10", "C50"])
    await expect(page.getByText(scale, { exact: true })).toBeVisible();
  await expect(page.getByText("No hardware or production claim")).toHaveCount(3);
  expect(await page.locator("article").count()).toBeLessThan(20);
});
