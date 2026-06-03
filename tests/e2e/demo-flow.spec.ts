import { expect, test } from "@playwright/test";

test("local demo flow confirms a match and updates ratings", async ({ page }) => {
  const runId = Date.now().toString(36);
  const ownerEmail = `owner-${runId}@example.com`;
  const opponentEmail = `opponent-${runId}@example.com`;
  const leagueName = `E2E Ladder ${runId}`;

  await page.goto("/demo");

  await page.getByLabel("Owner email").fill(ownerEmail);
  await page.getByLabel("Opponent email").fill(opponentEmail);
  await page.getByLabel("League name").fill(leagueName);
  await page.getByRole("button", { name: "Run full MVP flow" }).click();

  await expect(page.getByText("Demo complete. Ratings moved only after opponent confirmation.")).toBeVisible();
  await expect(page.getByText("COMPLETED")).toBeVisible();
  await expect(page.getByRole("cell", { name: "1016" }).first()).toBeVisible();
  await expect(page.getByRole("cell", { name: "984" }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Public page" })).toBeVisible();
});
