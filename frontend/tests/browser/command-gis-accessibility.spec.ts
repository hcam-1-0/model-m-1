import { expect, test } from "@playwright/test";
import axe from "axe-core";

for (const [name, url] of [
  ["command", "http://127.0.0.1:4173/command"],
  ["gis", "http://127.0.0.1:4174/gis"],
] as const) {
  test(`${name} workspace has accessible generated controls`, async ({ page, context }) => {
    await context.addInitScript({ content: axe.source });
    await page.goto(url);
    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).toBeVisible();
    const violations = await page.evaluate(async () => {
      const runner = (
        window as unknown as {
          axe: { run: () => Promise<{ violations: readonly { id: string }[] }> };
        }
      ).axe;
      return (await runner.run()).violations.map((item) => item.id);
    });
    expect(violations).toEqual([]);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
      ),
    ).toBe(false);
  });
}
