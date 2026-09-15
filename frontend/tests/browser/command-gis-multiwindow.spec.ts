import { expect, test } from "@playwright/test";

test("connected dashboard handoff opens a separate loopback workspace", async ({
  page,
  context,
}) => {
  await page.goto("/command");
  const [gis] = await Promise.all([
    context.waitForEvent("page"),
    page
      .getByRole("link", { name: /Open GIS Center/ })
      .first()
      .evaluate((element) => {
        (element as HTMLAnchorElement).target = "_blank";
        (element as HTMLAnchorElement).click();
      }),
  ]);
  await gis.waitForLoadState();
  await expect(gis).toHaveURL(/^http:\/\/127\.0\.0\.1:4174\/gis/);
  await expect(gis.getByRole("heading", { name: "GIS overview" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Command overview" })).toBeVisible();
  await gis.close();
});
