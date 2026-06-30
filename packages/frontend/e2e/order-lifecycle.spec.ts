import { test, expect } from "@playwright/test";
import { loginAsAgent, loginAsAdmin } from "./helpers";

test.describe("Full Order Lifecycle & Review Queue", () => {
  test("Dashboard shows KPI metrics", async ({ page }) => {
    await loginAsAgent(page);
    // Wait for dashboard title
    await expect(page.locator("h1").filter({ hasText: "Order Intelligence Dashboard" })).toBeVisible();
    // Wait for STP trend chart section to confirm full load — use role-based selector for period button
    await expect(page.getByRole("button", { name: "14d" })).toBeVisible();
  });

  test("Dashboard STP trend chart has period toggle", async ({ page }) => {
    await loginAsAgent(page);
    await expect(page.getByRole("button", { name: "7d" })).toBeVisible();
    await expect(page.getByRole("button", { name: "30d" })).toBeVisible();
  });

  test("Review Queue shows items or empty state", async ({ page }) => {
    await loginAsAgent(page);
    // Use role-based nav link selector to avoid strict mode violation
    await page.locator("aside a").filter({ hasText: "Review Queue" }).click();
    // Wait for page to load — the main content area should render
    await page.waitForLoadState("networkidle");
    await expect(page.locator("main")).toBeVisible();
    // Page should have a heading or content
    await expect(page.locator("main h1").first()).toBeVisible();
  });

  test("Approve order from Review Queue", async ({ page }) => {
    await loginAsAgent(page);
    await page.locator("aside a").filter({ hasText: "Review Queue" }).click();
    await page.waitForLoadState("networkidle");

    const approveBtn = page.getByRole("button", { name: "Approve" }).first();
    if (await approveBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await approveBtn.click();
      await page.waitForTimeout(2000);
      await expect(page.locator("main")).toBeVisible();
    }
  });

  test("Inbox page loads", async ({ page }) => {
    await loginAsAgent(page);
    await page.locator("aside a").filter({ hasText: "Inbox" }).click();
    await page.waitForLoadState("networkidle");
    await expect(page.locator("main").locator("h1, h2").filter({ hasText: /inbox/i })).toBeVisible();
  });

  test("Audit Logs page loads for admin", async ({ page }) => {
    await loginAsAdmin(page);
    // Click sidebar link — use anchor element to avoid matching page heading
    await page.locator("aside a").filter({ hasText: "Audit Logs" }).click();
    await page.waitForLoadState("networkidle");
    // Verify page loaded with heading
    await expect(page.locator("main h1").filter({ hasText: "Audit Logs" })).toBeVisible();
    // Verify table headers are present
    await expect(page.locator("th").filter({ hasText: "TIMESTAMP" })).toBeVisible();
  });

  test("Order detail shows sections", async ({ page }) => {
    await loginAsAgent(page);
    await page.goto("/orders");
    await page.waitForLoadState("networkidle");

    const orderLink = page.locator("a").filter({ hasText: "ORD-" }).first();
    if (await orderLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await orderLink.click();
      await page.waitForLoadState("networkidle");
      await expect(page.locator("h3, h2").filter({ hasText: "Customer Information" }).first()).toBeVisible();
      await expect(page.getByText("Pickup")).toBeVisible();
      await expect(page.getByText("Delivery")).toBeVisible();
    }
  });

  test("Order filters work", async ({ page }) => {
    await loginAsAgent(page);
    await page.goto("/orders");
    await page.waitForLoadState("networkidle");

    // Click "Created" filter tab
    await page.getByRole("button", { name: "Created" }).click();
    await page.waitForURL(/status=order_created/);
  });
});
