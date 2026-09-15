import { expect, test } from "@playwright/test";
import axe from "axe-core";
for (const route of ["/admin", "/admin/roles", "/admin/retention"] as const)
  test(`${route} has keyboard and table accessibility`, async ({ page, context }) => {
    await context.addInitScript({ content: axe.source });
    await page.goto(`http://127.0.0.1:4178${route}`);
    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).toBeVisible();
    const violations = await page.evaluate(async () =>
      (
        await (
          window as unknown as {
            axe: { run: () => Promise<{ violations: readonly { id: string }[] }> };
          }
        ).axe.run()
      ).violations.map((item) => item.id),
    );
    expect(violations).toEqual([]);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
      ),
    ).toBe(false);
  });
