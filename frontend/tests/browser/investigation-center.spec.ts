import { expect, test } from "@playwright/test";

test("Investigation Center presents authoritative chronology and exact reconstruction", async ({
  page,
}, testInfo) => {
  await page.goto("http://127.0.0.1:4176/investigations");
  await expect(page.getByRole("heading", { name: "Investigation overview" })).toBeVisible();
  await expect(page.getByText("Record sequence", { exact: true }).first()).toBeVisible();
  if ((page.viewportSize()?.width ?? 1000) <= 760)
    await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Reconstruction", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Exact revision reconstruction" })).toBeVisible();
  await expect(page.getByText(/Later records exist/)).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath(`investigation-reconstruction-${testInfo.project.name}.png`),
    fullPage: true,
  });
});

test("investigation queue drills into append-only detail", async ({ page }) => {
  await page.goto("http://127.0.0.1:4176/investigations/queue");
  await expect(page.getByRole("heading", { name: "Investigation queue" })).toBeVisible();
  await page.getByRole("link", { name: /Open Generated investigation 01/i }).click();
  await expect(page.getByText("GENERATED INVESTIGATION", { exact: true })).toBeVisible();
  await expect(page.getByText("Authority boundary")).toBeVisible();
});
