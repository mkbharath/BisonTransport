/**
 * API client for the Order Intelligence Platform backend.
 */

const API_BASE = "/api/v1";

let accessToken: string | null = null;

export function setToken(token: string | null) {
  accessToken = token;
}

export function getToken(): string | null {
  return accessToken;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      body?.error?.message || `HTTP ${response.status}`,
      body?.error?.code || "UNKNOWN"
    );
  }

  if (response.status === 204) return null as T;
  return response.json();
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// --- Auth ---
export async function login(email: string, password: string) {
  return request<{
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
  }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

// --- Orders ---
export async function createOrder(data: Record<string, unknown>) {
  return request<any>("/orders", { method: "POST", body: JSON.stringify(data) });
}

export async function getOrders(params?: Record<string, string | number>) {
  const query = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
  return request<{ data: any[]; total_count: number; total_pages: number; page: number; limit: number }>(`/orders${query}`);
}

export async function getOrder(id: string) {
  return request<any>(`/orders/${id}`);
}

export async function updateOrder(id: string, data: Record<string, unknown>) {
  return request<any>(`/orders/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}

export async function approveOrder(id: string) {
  return request<any>(`/orders/${id}/approve`, { method: "POST", body: JSON.stringify({}) });
}

export async function rejectOrder(id: string, comments?: string) {
  return request<any>(`/orders/${id}/reject`, {
    method: "POST",
    body: JSON.stringify({ comments: comments || null }),
  });
}

// --- Emails ---
export async function getEmails(params?: Record<string, string | number>) {
  const query = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
  return request<{ data: any[]; total_count: number; total_pages: number }>(`/emails${query}`);
}

export async function getEmail(id: string) {
  return request<any>(`/emails/${id}`);
}

// --- Queues ---
export async function getHitlQueue(params?: Record<string, string | number>) {
  const query = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
  return request<{ data: any[]; total_count: number; total_pages: number }>(`/queues/hitl${query}`);
}

export async function getHitlDetail(orderId: string) {
  return request<any>(`/queues/hitl/${orderId}`);
}

// --- Dashboard ---
export async function getDashboard() {
  return request<{
    total_orders: number;
    pending: number;
    awaiting_customer: number;
    auto_processed: number;
    stp_rate: number;
    hitl_queue_depth: number;
    completed: number;
    failed: number;
    avg_e2e_time: number;
    extraction_accuracy: number;
  }>("/reports/dashboard");
}

export async function getStpTrend(days: number = 7) {
  return request<{
    data: { date: string; total_orders: number; auto_processed: number; stp_rate: number }[];
    days: number;
  }>(`/reports/stp-trend?days=${days}`);
}

// --- Customers ---
export async function getCustomers(params?: Record<string, string | number>) {
  const query = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
  return request<{ data: any[]; total_count: number; total_pages: number }>(`/customers${query}`);
}

// --- Health ---
export async function getHealth() {
  return request<{ status: string; version: string; checks: Record<string, string> }>("/health");
}


// --- Admin: Audit Logs ---
export async function getAuditLogs(params?: Record<string, string | number>) {
  const query = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
  return request<{ data: any[]; total_count: number; total_pages: number; page: number; limit: number }>(`/admin/audit-logs${query}`);
}

// --- Admin: Field Configs ---
export async function getActiveFieldConfigs() {
  return request<{ data: any[] }>("/admin/field-configs/active");
}
export async function getFieldConfigs() {
  return request<{ data: any[] }>("/admin/field-configs");
}
export async function createFieldConfig(data: Record<string, unknown>) {
  return request<any>("/admin/field-configs", { method: "POST", body: JSON.stringify(data) });
}
export async function updateFieldConfig(id: string, data: Record<string, unknown>) {
  return request<any>(`/admin/field-configs/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}
export async function deleteFieldConfig(id: string) {
  return request<any>(`/admin/field-configs/${id}`, { method: "DELETE" });
}

// --- Admin: Business Rules ---
export async function getBusinessRules() {
  return request<{ data: any[] }>("/admin/business-rules");
}
export async function createBusinessRule(data: Record<string, unknown>) {
  return request<any>("/admin/business-rules", { method: "POST", body: JSON.stringify(data) });
}
export async function updateBusinessRule(id: string, data: Record<string, unknown>) {
  return request<any>(`/admin/business-rules/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}
export async function deleteBusinessRule(id: string) {
  return request<any>(`/admin/business-rules/${id}`, { method: "DELETE" });
}

// --- Admin: Email Templates ---
export async function getEmailTemplates() {
  return request<{ data: any[] }>("/admin/email-templates");
}
export async function createEmailTemplate(data: Record<string, unknown>) {
  return request<any>("/admin/email-templates", { method: "POST", body: JSON.stringify(data) });
}
export async function updateEmailTemplate(id: string, data: Record<string, unknown>) {
  return request<any>(`/admin/email-templates/${id}`, { method: "PATCH", body: JSON.stringify(data) });
}
export async function deleteEmailTemplate(id: string) {
  return request<any>(`/admin/email-templates/${id}`, { method: "DELETE" });
}
