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

test("portal exposes no external transport, secret, or effective action path", async ({ page }) => {
  const externalRequests: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (
      ["http:", "https:"].includes(url.protocol) &&
      !["127.0.0.1", "localhost"].includes(url.hostname)
    )
      externalRequests.push(url.origin);
  });
  await page.goto("/");
  const body = await page.locator("body").innerText();
  expect(body).not.toMatch(/rtsp:\/\/|whep:\/\/|BEGIN PRIVATE KEY|Bearer\s+[A-Za-z0-9._-]+/iu);
  expect(await page.locator("a[download], input[type=password]").count()).toBe(0);
  expect(externalRequests).toEqual([]);
  expect(
    await page.evaluate(() =>
      [...Object.keys(localStorage), ...Object.keys(sessionStorage)].every(
        (key) => !/token|secret|credential|identity|media/iu.test(key),
      ),
    ),
  ).toBe(true);
});
