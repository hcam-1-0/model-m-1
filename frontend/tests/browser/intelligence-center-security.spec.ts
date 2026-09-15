import { expect, test } from "@playwright/test";
test("browser projection has no sensitive fields or external requests", async ({ page }) => {
  const external: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.hostname !== "127.0.0.1") external.push(request.url());
  });
  await page.goto("http://127.0.0.1:4175/intelligence/candidates/SYN-CANDIDATE-0001");
  const text = await page.locator("body").innerText();
  expect(text).not.toMatch(
    /password|credential|biometric template|vehicle plate|provider payload/iu,
  );
  expect(text).toMatch(/Identity not established/i);
  expect(external).toEqual([]);
});
