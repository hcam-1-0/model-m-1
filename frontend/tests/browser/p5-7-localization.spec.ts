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

test("browser supports the frozen locale and timezone projections", async ({ page }) => {
  await page.goto("/");
  const result = await page.evaluate(() => {
    const instant = new Date("2026-09-12T06:30:00.000Z");
    return ["en-IN", "gu-IN", "hi-IN"].map((locale) =>
      new Intl.DateTimeFormat(locale, {
        dateStyle: "medium",
        timeStyle: "medium",
        timeZone: "Asia/Kolkata",
      }).format(instant),
    );
  });
  expect(result).toHaveLength(3);
  expect(result.every((value) => value.length > 8)).toBe(true);
});
