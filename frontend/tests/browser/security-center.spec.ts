import { expect, test } from "@playwright/test";
test("Security Center separates assurance and audit lanes", async ({ page }, testInfo) => {
  await page.goto("http://127.0.0.1:4179/security");
  await expect(page.getByRole("heading", { name: "Security overview" })).toBeVisible();
  await expect(page.getByText("Assurance boundary")).toBeVisible();
  if ((page.viewportSize()?.width ?? 1000) <= 820)
    await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Supply chain" }).click();
  await expect(page.getByRole("heading", { name: "Supply-chain assurance" })).toBeVisible();
  await expect(page.getByText("Stale assurance evidence")).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath(`security-supply-chain-${testInfo.project.name}.png`),
    fullPage: true,
  });
});
