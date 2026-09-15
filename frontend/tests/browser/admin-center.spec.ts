import { expect, test } from "@playwright/test";
test("Admin Center presents non-effective governance and independent approvals", async ({
  page,
}, testInfo) => {
  await page.goto("http://127.0.0.1:4178/admin");
  await expect(page.getByRole("heading", { name: "Administration overview" })).toBeVisible();
  await expect(page.getByText("Server decisions only")).toBeVisible();
  if ((page.viewportSize()?.width ?? 1000) <= 820)
    await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Change requests" }).click();
  await expect(page.getByRole("heading", { name: "Policy and change requests" })).toBeVisible();
  await expect(page.getByText("No effective mutation").first()).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath(`admin-change-control-${testInfo.project.name}.png`),
    fullPage: true,
  });
});
