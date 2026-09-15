import { expect, test } from "@playwright/test";
test("Platform Operations preserves monitoring and adds qualified platform health", async ({
  page,
}, testInfo) => {
  await page.goto("http://127.0.0.1:4180/operations/platform");
  await expect(page.getByRole("heading", { name: "Platform operations" })).toBeVisible();
  await expect(page.getByText(/not live telemetry/i)).toBeVisible();
  if ((page.viewportSize()?.width ?? 1000) <= 820)
    await page.getByRole("button", { name: "Open navigation" }).click();
  await page
    .getByRole("navigation", { name: "Operations navigation" })
    .getByRole("link", { name: "Queues and workers" })
    .click();
  await expect(page.getByRole("heading", { name: "Queues, workers, and circuits" })).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath(`platform-queues-${testInfo.project.name}.png`),
    fullPage: true,
  });
});
