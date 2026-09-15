import { expect, test } from "@playwright/test";
for (const [profile, viewport] of [
  ["C1", { width: 390, height: 844 }],
  ["C10", { width: 1280, height: 720 }],
  ["C50", { width: 1920, height: 1080 }],
] as const)
  test(`${profile} viewport remains stable and complete`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto("http://127.0.0.1:4175/intelligence/relationships");
    await expect(page.getByRole("heading", { name: "Relationship explorer" })).toBeVisible();
    await expect(page.getByText("Relationship nodes")).toBeVisible();
    await expect(page.getByText("Relationship edges")).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
      ),
    ).toBe(false);
  });
