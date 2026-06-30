import { test, expect } from "@playwright/test";
import { loginAsAdmin, loginAsAgent } from "./helpers";

test.describe("Admin Field Config → New Order Form", () => {
  test("Admin can see Field Configuration tab", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin");
    await expect(page.getByRole("button", { name: "Field Configuration" })).toBeVisible();
    await expect(page.getByText("customer_name")).toBeVisible();
  });

  test("Admin can add a new field", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin");

    // Wait for the table to load
    await expect(page.getByText("customer_name")).toBeVisible();

    // Click Add Field button
    await page.getByRole("button", { name: "Add Field" }).click();

    // Wait for the inline form to appear — identified by h3 "Add Field" heading inside it
    const formContainer = page.locator("div.border.rounded-xl").filter({ has: page.locator("h3") });
    await expect(formContainer).toBeVisible();

    // Fill form inputs — the form grid has: Field Name (text), Label (text), Display Order (number)
    const allInputs = formContainer.locator(".grid input");
    await allInputs.nth(0).fill("test_carrier_ref");
    await allInputs.nth(1).fill("Test Carrier Reference");
    await allInputs.nth(2).clear();
    await allInputs.nth(2).fill("71");

    // Check mandatory checkbox
    const mandatoryCheckbox = formContainer.locator("label").filter({ hasText: "Mandatory" }).locator("input[type='checkbox']");
    await mandatoryCheckbox.check();

    // Save — click "Create" button
    await formContainer.getByRole("button", { name: "Create" }).click();
    await page.waitForTimeout(2000);

    // Verify it appears in the table
    await expect(page.getByText("test_carrier_ref")).toBeVisible();
  });

  test("Mandatory field validation blocks form without value", async ({ page }) => {
    await loginAsAgent(page);
    await page.goto("/orders/new");

    // Wait for dynamic form to load
    await page.waitForSelector("h3", { timeout: 10_000 });

    // Try to click Next without filling mandatory fields — should stay on same step
    await page.getByRole("button", { name: "Next" }).click();
    await page.waitForTimeout(500);

    // Should still be on step 1 (Customer Info heading visible)
    await expect(page.locator("h3").filter({ hasText: "Customer Information" })).toBeVisible();
  });

  test("Conditional field shows/hides based on equipment type", async ({ page }) => {
    await loginAsAgent(page);
    await page.goto("/orders/new");
    await page.waitForSelector("h3", { timeout: 10_000 });

    // Fill step 1 minimally — just the first visible text input
    const step1Input = page.locator("main input[type='text']:visible").first();
    await step1Input.fill("Conditional Test");
    await page.getByRole("button", { name: "Next" }).click();
    await page.waitForTimeout(500);

    // Step 2: Pickup — fill visible text inputs
    const step2Inputs = page.locator("main input[type='text']:visible");
    for (let i = 0; i < Math.min(await step2Inputs.count(), 2); i++) {
      if (await step2Inputs.nth(i).isVisible()) await step2Inputs.nth(i).fill("X");
    }
    await page.getByRole("button", { name: "Next" }).click();
    await page.waitForTimeout(500);

    // Step 3: Delivery
    const step3Inputs = page.locator("main input[type='text']:visible");
    for (let i = 0; i < Math.min(await step3Inputs.count(), 2); i++) {
      if (await step3Inputs.nth(i).isVisible()) await step3Inputs.nth(i).fill("Y");
    }
    await page.getByRole("button", { name: "Next" }).click();
    await page.waitForTimeout(500);

    // Now on step 4 (Shipment)
    // Temperature fields should NOT be visible initially
    const tempLabel = page.getByText("Temperature Min");
    await expect(tempLabel).not.toBeVisible();

    // Select Reefer equipment if the select exists
    const equipSelect = page.locator("select").filter({ has: page.locator("option[value='reefer']") });
    if (await equipSelect.isVisible()) {
      await equipSelect.selectOption("reefer");
      await expect(page.getByText("Temperature Min")).toBeVisible({ timeout: 3_000 });
    }
  });

  test("Admin can delete a field", async ({ page }) => {
    await loginAsAdmin(page);
    await page.goto("/admin");

    // Wait for table to load
    await expect(page.getByText("customer_name")).toBeVisible();

    // Find the test_carrier_ref field row
    const row = page.locator("tr").filter({ hasText: "test_carrier_ref" });
    if (await row.isVisible()) {
      // Click delete (last button in row)
      await row.locator("button").last().click();
      await page.waitForTimeout(1000);
      // Verify it's gone
      await expect(page.getByText("test_carrier_ref")).not.toBeVisible();
    }
  });
});
