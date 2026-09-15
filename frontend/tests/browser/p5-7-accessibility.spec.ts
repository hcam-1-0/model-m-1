import { expect, test } from "@playwright/test";
import axe from "axe-core";

test.beforeEach(async ({ page }) => {
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (
      ["http:", "https:"].includes(url.protocol) &&
      !["127.0.0.1", "localhost"].includes(url.hostname)
    ) {
      await route.abort("blockedbyclient");
      return;
    }
    await route.continue();
  });
});

test("portal has automated and keyboard accessibility evidence", async ({ page, context }) => {
  await context.addInitScript({ content: axe.source });
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toBeVisible();
  const violations = await page.evaluate(async () => {
    const runner = (
      window as unknown as {
        axe: {
          run: () => Promise<{
            violations: readonly {
              id: string;
              nodes: readonly { target: readonly string[] }[];
            }[];
          }>;
        };
      }
    ).axe;
    return (await runner.run()).violations.map(({ id, nodes }) => ({
      id,
      targets: nodes.map(({ target }) => target.join(" ")),
    }));
  });
  expect(violations).toEqual([]);
  await expect(page.locator("main")).toHaveCount(1);
});
