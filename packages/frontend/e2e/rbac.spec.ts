import { test, expect } from "@playwright/test";
import { loginAsAgent, loginAsAdmin, loginAsSupervisor } from "./helpers";

test.describe("Role-Based Access Control", () => {
  test("Agent sees correct nav items — no Admin", async ({ page }) => {
    await loginAsAgent(page);

    const sidebar = page.locator("aside");
    await expect(sidebar.locator("a").filter({ hasText: "Dashboard" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Orders" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Inbox" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Review Queue" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Administration" })).not.toBeVisible();
  });

  test("Supervisor sees Audit Logs but not Administration", async ({ page }) => {
    await loginAsSupervisor(page);

    const sidebar = page.locator("aside");
    await expect(sidebar.locator("a").filter({ hasText: "Dashboard" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Audit Logs" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Administration" })).not.toBeVisible();
  });

  test("Admin sees all nav items including Administration", async ({ page }) => {
    await loginAsAdmin(page);

    const sidebar = page.locator("aside");
    await expect(sidebar.locator("a").filter({ hasText: "Dashboard" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Orders" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Inbox" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Review Queue" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Audit Logs" })).toBeVisible();
    await expect(sidebar.locator("a").filter({ hasText: "Administration" })).toBeVisible();
  });

  test("Agent cannot see admin nav item", async ({ page }) => {
    await loginAsAgent(page);
    await expect(page.locator("aside a").filter({ hasText: "Administration" })).not.toBeVisible();
  });

  test("Agent can see Review Queue page", async ({ page }) => {
    await loginAsAgent(page);
    await page.locator("aside a").filter({ hasText: "Review Queue" }).click();
    await page.waitForLoadState("networkidle");
    // Should load the page with a heading
    await expect(page.locator("main h1").first()).toBeVisible();
  });

  test("Login page shows demo credentials", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("Demo")).toBeVisible();
    await expect(page.getByText("agent@test.com")).toBeVisible();
  });

  test("Invalid credentials show error", async ({ page }) => {
    await page.goto("/login");
    await page.getByPlaceholder("you@company.com").fill("wrong@test.com");
    await page.getByPlaceholder("Enter your password").fill("wrongpass");
    await page.getByRole("button", { name: "Sign In" }).click();
    await expect(page.getByText(/failed|invalid|error/i)).toBeVisible({ timeout: 10_000 });
  });

  test("Logout redirects to login page", async ({ page }) => {
    await loginAsAgent(page);
    await page.getByTitle("Sign out").click();
    await page.waitForURL("/login");
  });
});
