import { expect, test } from "@playwright/test";

test("independent windows do not share transient grants", async ({ page, context }) => {
  await page.goto("/command");
  await page.evaluate(() => {
    Object.defineProperty(window, "__hcamGeneratedGrant", {
      configurable: true,
      value: "window-one-memory-only",
    });
  });
  const second = await context.newPage();
  await second.goto("/command");
  expect(await second.evaluate(() => "__hcamGeneratedGrant" in window)).toBe(false);
  expect(
    await second.evaluate(() =>
      JSON.stringify({ local: Object.keys(localStorage), session: Object.keys(sessionStorage) }),
    ),
  ).not.toMatch(/grant|g1_/i);
  await second.close();
  await expect(page.getByRole("heading", { name: "Command Center" })).toBeVisible();
});
