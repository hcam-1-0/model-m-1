import { expect, test } from "@playwright/test";

test("Investigation Center supports keyboard and table-first workflows", async ({ page }) => {
  await page.goto("http://127.0.0.1:4176/investigations/timeline");
  await expect(page.getByRole("table")).toBeVisible();
  await page.keyboard.press("Control+K");
  await expect(page.getByRole("dialog", { name: "Investigation search" })).toBeVisible();
  await expect(
    page.getByRole("textbox", { name: "Search generated investigations" }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Investigation search" })).toBeHidden();
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus-visible")).toHaveCount(1);
});
