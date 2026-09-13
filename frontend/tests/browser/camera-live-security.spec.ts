import { expect, test } from "@playwright/test";

test("camera navigation contains no media grants or control commands", async ({ page }) => {
  const requested: string[] = [];
  page.on("request", (request) => requested.push(request.url()));
  await page.goto("/command/cameras");
  const serializedStorage = await page.evaluate(() =>
    JSON.stringify({ local: Object.keys(localStorage), session: Object.keys(sessionStorage) }),
  );
  expect(serializedStorage).not.toMatch(/g1_|rtsp|password|secret/i);
  expect(requested.join("\n")).not.toMatch(/[?&](?:token|grant|secret)=/i);
  await expect(
    page.getByRole("button", { name: /record|snapshot|download|export|print|ptz/i }),
  ).toHaveCount(0);
});
