import { expect, test } from "@playwright/test";

test("Evidence Desk separates states and preserves opaque sources", async ({ page }, testInfo) => {
  await page.goto("http://127.0.0.1:4177/evidence");
  await expect(page.getByRole("heading", { name: "Evidence reference overview" })).toBeVisible();
  await page.getByRole("link", { name: /Open Generated evidence reference 01/i }).click();
  await expect(page.getByRole("heading", { name: "Evidence state matrix" })).toBeVisible();
  await expect(page.getByText("No combined verification conclusion")).toBeVisible();
  await expect(page.getByText("not exposed")).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath(`evidence-detail-${testInfo.project.name}.png`),
    fullPage: true,
  });
});

test("Evidence Desk presents provenance and custody with authoritative tables", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:4177/evidence/provenance");
  await expect(page.getByRole("heading", { name: "Provenance and custody" })).toBeVisible();
  await expect(page.getByLabel("Generated provenance visual projection")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Node-edge table" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Custody event table" })).toBeVisible();
});
