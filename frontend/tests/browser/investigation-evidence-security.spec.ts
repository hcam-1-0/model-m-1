import { expect, test } from "@playwright/test";

test("Evidence Desk exposes no source, media, or operational action", async ({ page }) => {
  await page.goto("http://127.0.0.1:4177/evidence/SYN-EVIDENCE-0001");
  await expect(page.locator("video, audio, img[src], a[download]")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: /download|export|print|delete|hold|release|resolve|render/i }),
  ).toHaveCount(0);
  await expect(
    page.getByText(
      /Integrity is not truth, authenticity, identity, guilt, legal admissibility, or proof/,
    ),
  ).toBeVisible();
  const body = await page.locator("body").innerText();
  expect(body).not.toMatch(/rtsp:\/\/|whep:\/\/|file:\/\/|password|secret_ref|credential/i);
});
