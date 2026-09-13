import { expect, test } from "@playwright/test";

test("Evidence Desk supports keyboard search and table alternatives", async ({ page }) => {
  await page.goto("http://127.0.0.1:4177/evidence/queue");
  await expect(page.getByRole("table")).toBeVisible();
  await page.keyboard.press("Control+K");
  await expect(page.getByRole("dialog", { name: "Evidence search" })).toBeVisible();
  await expect(
    page.getByRole("textbox", { name: "Search generated evidence references" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Evidence search" })).toBeHidden();
});
