import { Page } from "@playwright/test";

const API_BASE = "http://localhost:8000/api/v1";

/**
 * Login as a specific user and store the JWT.
 */
export async function login(page: Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByPlaceholder("you@company.com").fill(email);
  await page.getByPlaceholder("Enter your password").fill(password);
  await page.getByRole("button", { name: "Sign In" }).click();
  // Wait for redirect to dashboard
  await page.waitForURL("/");
}

export async function loginAsAgent(page: Page) {
  await login(page, "agent@test.com", "agent123");
}

export async function loginAsAdmin(page: Page) {
  await login(page, "admin@test.com", "admin123");
}

export async function loginAsSupervisor(page: Page) {
  await login(page, "supervisor@test.com", "super123");
}

/**
 * Get an auth token directly from the API (for API-level setup/teardown).
 */
export async function getAuthToken(email: string, password: string): Promise<string> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  return data.access_token;
}

/**
 * Make an authenticated API call.
 */
export async function apiCall(
  token: string,
  method: string,
  path: string,
  body?: Record<string, unknown>
): Promise<unknown> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  return res.json();
}

/**
 * Clean up test data: delete orders and field configs created during tests.
 */
export async function cleanupTestData(token: string) {
  // We don't do destructive cleanup — tests should be idempotent
}
