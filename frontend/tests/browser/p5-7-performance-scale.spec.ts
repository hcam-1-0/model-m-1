import { expect, test } from "@playwright/test";

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

test("generated portal stays inside context-qualified browser bounds", async ({ page }) => {
  await page.goto("/");
  const observation = await page.evaluate(() => ({
    nodes: document.querySelectorAll("*").length,
    resources: performance.getEntriesByType("resource").length,
    navigationMs: Math.round(performance.getEntriesByType("navigation")[0]?.duration ?? 0),
  }));
  expect(observation.nodes).toBeLessThan(5000);
  expect(observation.resources).toBeLessThan(250);
  expect(observation.navigationMs).toBeLessThan(5000);
});
