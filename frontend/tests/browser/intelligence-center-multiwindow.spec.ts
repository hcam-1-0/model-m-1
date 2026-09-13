import { expect, test } from "@playwright/test";
test("Command remains primary and Intelligence links only to specialist centers", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:4175/intelligence");
  await expect(page.getByRole("link", { name: /Command Center/ })).toHaveAttribute(
    "href",
    "http://127.0.0.1:4173/command",
  );
  await expect(page.getByRole("link", { name: /GIS Center/ })).toHaveAttribute(
    "href",
    "http://127.0.0.1:4174/gis",
  );
  if ((page.viewportSize()?.width ?? 1000) <= 820)
    await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Spatial intelligence" }).click();
  await expect(page.getByRole("heading", { name: "Spatial intelligence" })).toBeVisible();
});
