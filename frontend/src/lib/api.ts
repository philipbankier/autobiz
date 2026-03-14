import { getToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  meta: Record<string, unknown> | null;
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    const body = await response.json().catch(() => ({}));

    if (!response.ok) {
      return {
        data: null,
        error: body.detail || body.error || `HTTP ${response.status}`,
        meta: null,
      };
    }

    // Backend wraps responses in {data, error, meta}
    if (body.data !== undefined) {
      return body as ApiResponse<T>;
    }
    return { data: body as T, error: null, meta: null };
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : "Network error",
      meta: null,
    };
  }
}

// === Auth ===

export interface AuthResponse {
  user: {
    id: string;
    email: string;
    name: string;
    credits_balance: string;
  };
  access_token: string;
  token_type: string;
}

export async function login(email: string, password: string) {
  return fetchApi<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function register(email: string, password: string, name: string) {
  return fetchApi<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name }),
  });
}

export async function getMe() {
  return fetchApi<{ id: string; email: string; name: string; credits_balance: string }>("/api/auth/me");
}

// === Companies ===

export interface Company {
  id: string;
  user_id: string;
  name: string;
  mission: string;
  slug: string;
  status: string;
  config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export async function getCompanies() {
  return fetchApi<Company[]>("/api/companies");
}

export async function getCompany(id: string) {
  return fetchApi<Company>(`/api/companies/${id}`);
}

export async function createCompany(name: string, mission: string, slug: string) {
  return fetchApi<Company>("/api/companies", {
    method: "POST",
    body: JSON.stringify({ name, mission, slug }),
  });
}

// === Dashboard ===

export interface DashboardData {
  company_status: string;
  departments: { type: string; status: string }[];
  active_runs: number;
  completed_runs: number;
  task_stats: Record<string, number>;
  total_cost: string;
  credits_balance: string;
}

export async function getDashboard(companyId: string) {
  return fetchApi<DashboardData>(`/api/companies/${companyId}/dashboard`);
}

// === Departments ===

export interface Department {
  id: string;
  company_id: string;
  type: string;
  autonomy_level: string;
  budget_cap_daily: string | null;
  status: string;
  agent_session_id: string | null;
  created_at: string;
  updated_at: string;
}

export async function getDepartments(companyId: string) {
  return fetchApi<Department[]>(`/api/companies/${companyId}/departments`);
}

export async function updateDepartment(companyId: string, deptType: string, data: { autonomy_level?: string; budget_cap_daily?: number | null }) {
  return fetchApi<Department>(`/api/companies/${companyId}/departments/${deptType}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function triggerDepartment(companyId: string, deptType: string) {
  return fetchApi<{ task_id: string; department: string; status: string }>(`/api/companies/${companyId}/departments/${deptType}/trigger`, {
    method: "POST",
  });
}

// === Activity ===

export interface AgentRun {
  id: string;
  department_id: string;
  company_id: string;
  trigger: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  tokens_used: number;
  cost: string;
  summary: string | null;
}

export async function getActivity(companyId: string, limit = 20, offset = 0) {
  return fetchApi<AgentRun[]>(`/api/companies/${companyId}/activity?limit=${limit}&offset=${offset}`);
}

// === Tasks ===

export interface AgentTask {
  id: string;
  company_id: string;
  department_id: string | null;
  title: string;
  description: string;
  status: string;
  priority: string;
  created_by: string;
  assigned_department: string;
  created_at: string;
  completed_at: string | null;
}

export async function getTasks(companyId: string) {
  return fetchApi<AgentTask[]>(`/api/companies/${companyId}/tasks`);
}

export async function createTask(companyId: string, data: { title: string; description: string; priority: string; assigned_department: string }) {
  return fetchApi<AgentTask>(`/api/companies/${companyId}/tasks`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// === Chat ===

export interface AgentMessage {
  id: string;
  company_id: string;
  department_id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface ChatResponse {
  user_message: AgentMessage;
  agent_message: AgentMessage;
}

export async function getChat(companyId: string, departmentType?: string) {
  const params = departmentType ? `?department_type=${departmentType}` : "";
  return fetchApi<AgentMessage[]>(`/api/companies/${companyId}/chat${params}`);
}

export async function sendChat(companyId: string, departmentType: string, content: string) {
  return fetchApi<ChatResponse>(`/api/companies/${companyId}/chat`, {
    method: "POST",
    body: JSON.stringify({ department_type: departmentType, content }),
  });
}

// === Billing ===

export async function getBalance() {
  return fetchApi<{ credits_balance: string }>("/api/billing/balance");
}

export async function getUsage() {
  return fetchApi<{ total_cost: string; breakdown: Record<string, string> }>("/api/billing/usage");
}

// === Onboarding ===

export async function onboardCompany(companyId: string) {
  return fetchApi<{ status: string }>(`/api/companies/${companyId}/onboard`, {
    method: "POST",
  });
}

export async function getCompanyFile(companyId: string, path: string) {
  return fetchApi<{ content: string }>(`/api/companies/${companyId}/files/${encodeURIComponent(path)}`);
}

export function connectActivityStream(
  companyId: string,
  onEvent: (event: Record<string, unknown>) => void
): EventSource {
  const token = getToken();
  const url = `${API_URL}/api/companies/${companyId}/activity/stream${token ? `?token=${token}` : ""}`;
  const es = new EventSource(url);

  es.onmessage = (msg) => {
    try {
      const parsed = JSON.parse(msg.data);
      onEvent(parsed);
    } catch {
      onEvent({ type: "raw", data: msg.data });
    }
  };

  es.onerror = () => {
    onEvent({ type: "error", message: "Connection lost. Events may have been missed." });
  };

  return es;
}
