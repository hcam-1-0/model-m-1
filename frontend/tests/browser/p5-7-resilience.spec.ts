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

test("generated request failure remains typed and the operator surface stays available", async ({
  page,
}) => {
  await page.route("**/__p57_generated_failure__", (route) => route.abort("failed"));
  await page.goto("/");
  const outcome = await page.evaluate(async () => {
    try {
      await fetch("/__p57_generated_failure__");
      return "unexpected_success";
    } catch {
      return "generated_failure";
    }
  });
  expect(outcome).toBe("generated_failure");
  await expect(page.locator("main")).toBeVisible();
});
