import { expect, test } from "@playwright/test";

test("Investigation Center exposes deterministic C1 C10 C50 workload ceilings", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:4176/investigations");
  await expect(page.getByText("C1 / C10 / C50", { exact: true })).toBeVisible();
  await expect(page.getByText("200 records", { exact: true })).toBeVisible();
});
