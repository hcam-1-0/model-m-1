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

test("viewport projection has no page-level overflow or incoherent overlap", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("main")).toBeVisible();
  const geometry = await page.evaluate(() => ({
    documentWidth: document.documentElement.scrollWidth,
    viewportWidth: document.documentElement.clientWidth,
    main: (() => {
      const rect = document.querySelector("main")?.getBoundingClientRect();
      return rect
        ? { width: rect.width, height: rect.height, left: rect.left, right: rect.right }
        : null;
    })(),
    overflowCandidates: [...document.querySelectorAll<HTMLElement>("body *")]
      .map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          tag: element.tagName.toLowerCase(),
          className: (element.getAttribute("class") ?? "").slice(0, 80),
          left: Math.round(rect.left),
          right: Math.round(rect.right),
          width: Math.round(rect.width),
          scrollWidth: element.scrollWidth,
        };
      })
      .filter(
        ({ left, right, width, scrollWidth }) =>
          left < 0 || right > window.innerWidth + 1 || scrollWidth > width + 2,
      )
      .slice(0, 12),
  }));
  expect(geometry.documentWidth, JSON.stringify(geometry.overflowCandidates)).toBeLessThanOrEqual(
    geometry.viewportWidth + 1,
  );
  expect(geometry.main?.width ?? 0).toBeGreaterThan(0);
  expect(geometry.main?.height ?? 0).toBeGreaterThan(0);
  expect(geometry.main?.left ?? -1).toBeGreaterThanOrEqual(0);
  expect(geometry.main?.right ?? Number.MAX_SAFE_INTEGER).toBeLessThanOrEqual(
    geometry.viewportWidth + 1,
  );
});
