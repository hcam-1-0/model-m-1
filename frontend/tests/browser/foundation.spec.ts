import { expect, test } from "@playwright/test";
import axe from "axe-core";
test("desktop shell is visible, keyboard reachable, and bounded", async ({
  page,
  context,
}, testInfo) => {
  await context.addInitScript({ content: axe.source });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: "Command Center" })).toBeVisible();
  await expect(page.getByText("Generated environment. No operational data.")).toBeVisible();
  await page.keyboard.press("Control+k");
  await expect(page.getByRole("dialog", { name: "Command search" })).toBeVisible();
  await expect(page.getByRole("searchbox")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(overflow).toBe(false);
  const violations = await page.evaluate(async () => {
    const runner = (
      window as unknown as {
        axe: { run: () => Promise<{ violations: readonly { readonly id: string }[] }> };
      }
    ).axe;
    return (await runner.run()).violations.map((violation) => violation.id);
  });
  expect(violations).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath("foundation.png"), fullPage: true });
});
test("mobile navigation does not occlude the workspace", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile", "mobile-only assertion");
  await page.goto("/");
  const menu = page.getByRole("button", { name: "Open navigation" });
  await expect(menu).toBeVisible();
  await menu.click();
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(menu).toHaveAttribute("aria-expanded", "false");
  await page.screenshot({ path: testInfo.outputPath("mobile-navigation.png"), fullPage: true });
});
test("reduced motion and forced colors preserve complete reflow", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce", forcedColors: "active" });
  await page.setViewportSize({ width: 640, height: 800 });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: "Command Center" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Open navigation" })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
    ),
  ).toBe(false);
});
