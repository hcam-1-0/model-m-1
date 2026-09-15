import { expect, test } from "@playwright/test";
test("Intelligence Center presents typed queues and bounded human review", async ({
  page,
}, testInfo) => {
  await page.goto("http://127.0.0.1:4175/intelligence");
  await expect(page.getByRole("heading", { name: "Intelligence overview" })).toBeVisible();
  await expect(
    page.getByText("Identity not established across all generated candidates."),
  ).toBeVisible();
  if ((page.viewportSize()?.width ?? 1000) <= 820)
    await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Mandatory review" }).click();
  await expect(page.getByRole("heading", { name: "Mandatory review desk" })).toBeVisible();
  await page.getByRole("button", { name: "Review generated proposal" }).click();
  await expect(page.getByRole("heading", { name: "Confirm review decision" })).toBeVisible();
  await page.getByRole("button", { name: "Record generated review" }).click();
  await expect(page.getByText("Generated review receipt recorded")).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath(`intelligence-review-${testInfo.project.name}.png`),
    fullPage: true,
  });
});
test("typed queue drills into a bounded hypothesis", async ({ page }) => {
  await page.goto("http://127.0.0.1:4175/intelligence/hypotheses");
  await expect(page.getByRole("heading", { name: "Hypothesis queue" })).toBeVisible();
  await page.getByRole("link", { name: /Open hypothesis 01/i }).click();
  await expect(page.getByText("WORKING ANALYTICAL PROPOSITION")).toBeVisible();
  await expect(page.getByText("not established")).toBeVisible();
});
