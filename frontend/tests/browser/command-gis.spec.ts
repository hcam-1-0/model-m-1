import { expect, test } from "@playwright/test";

test("Command Center is primary and GIS Center is connected", async ({ page }, testInfo) => {
  await page.goto("/command");
  await expect(page.getByRole("heading", { name: "Command overview" })).toBeVisible();
  await expect(page.getByText("Blocked producer gaps")).toBeVisible();
  await expect(page.getByRole("link", { name: /Open GIS Center/ }).first()).toHaveAttribute(
    "href",
    "http://127.0.0.1:4174/gis",
  );
  await page.screenshot({ path: testInfo.outputPath("command-center.png"), fullPage: true });
  await page.goto("http://127.0.0.1:4174/gis");
  await expect(page.getByRole("heading", { name: "GIS overview" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Generated spatial records" })).toBeVisible();
  await expect(page.getByText("External sources")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("gis-center.png"), fullPage: true });
});

test("GIS map and authoritative table synchronize selection", async ({ page }) => {
  await page.goto("http://127.0.0.1:4174/gis");
  await page.getByRole("button", { name: "Generated sector A-1" }).click();
  await expect(page.getByRole("heading", { name: "Generated sector A-1" })).toBeVisible();
  await page.getByRole("textbox", { name: "Filter generated map records" }).fill("B-2");
  await expect(page.getByText("1 records")).toBeVisible();
});
