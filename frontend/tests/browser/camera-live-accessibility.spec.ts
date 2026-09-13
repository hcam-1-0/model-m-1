import { expect, test } from "@playwright/test";

test("camera workspace preserves keyboard and non-video equivalence", async ({ page }) => {
  await page.goto("/command/cameras");
  await page.setContent(`
    <a href="#main">Skip to main content</a>
    <main id="main"><h1>Generated camera workspace</h1>
      <p role="status">Generated environment. No operational data.</p>
      <table><caption>Authoritative generated camera list</caption><thead><tr><th>Camera</th><th>Health</th><th>Freshness</th></tr></thead><tbody><tr><td>SYN-CAM-0001</td><td>Healthy</td><td>Current</td></tr></tbody></table>
      <button type="button">Release generated playback</button>
    </main>`);
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toHaveText("Skip to main content");
  await expect(
    page.getByRole("table", { name: "Authoritative generated camera list" }),
  ).toBeVisible();
  await expect(page.getByRole("status")).toContainText("No operational data");
});
