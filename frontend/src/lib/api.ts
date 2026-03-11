import { getToken } from "./auth";
import type {
  ApiResponse,
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  Company,
  CreateCompanyRequest,
  Department,
  UpdateDepartmentRequest,
  AgentRun,
  AgentTask,
  CreateTaskRequest,
  AgentMessage,
  SendMessageRequest,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      return {
        data: null,
        error: errorBody.detail || errorBody.message || `HTTP ${response.status}`,
        meta: null,
      };
    }

    const data = await response.json();
    return { data, error: null, meta: null };
  } catch (error) {
    return {
      data: null,
      error: error instanceof Error ? error.message : "Network error",
      meta: null,
    };
  }
}

// === Auth ===

export async function login(req: LoginRequest): Promise<ApiResponse<AuthResponse>> {
  return fetchApi<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function register(req: RegisterRequest): Promise<ApiResponse<AuthResponse>> {
  return fetchApi<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// === Companies ===

export async function getCompanies(): Promise<ApiResponse<Company[]>> {
  return fetchApi<Company[]>("/companies");
}

export async function getCompany(id: string): Promise<ApiResponse<Company>> {
  return fetchApi<Company>(`/companies/${id}`);
}

export async function createCompany(req: CreateCompanyRequest): Promise<ApiResponse<Company>> {
  return fetchApi<Company>("/companies", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// === Departments ===

export async function getDepartments(companyId: string): Promise<ApiResponse<Department[]>> {
  return fetchApi<Department[]>(`/companies/${companyId}/departments`);
}

export async function updateDepartment(
  companyId: string,
  departmentId: string,
  req: UpdateDepartmentRequest
): Promise<ApiResponse<Department>> {
  return fetchApi<Department>(`/companies/${companyId}/departments/${departmentId}`, {
    method: "PATCH",
    body: JSON.stringify(req),
  });
}

// === Agent Runs ===

export async function getAgentRuns(companyId: string): Promise<ApiResponse<AgentRun[]>> {
  return fetchApi<AgentRun[]>(`/companies/${companyId}/runs`);
}

// === Tasks ===

export async function getTasks(companyId: string): Promise<ApiResponse<AgentTask[]>> {
  return fetchApi<AgentTask[]>(`/companies/${companyId}/tasks`);
}

export async function createTask(
  companyId: string,
  req: CreateTaskRequest
): Promise<ApiResponse<AgentTask>> {
  return fetchApi<AgentTask>(`/companies/${companyId}/tasks`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function updateTaskStatus(
  companyId: string,
  taskId: string,
  status: string
): Promise<ApiResponse<AgentTask>> {
  return fetchApi<AgentTask>(`/companies/${companyId}/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

// === Chat ===

export async function getMessages(companyId: string): Promise<ApiResponse<AgentMessage[]>> {
  return fetchApi<AgentMessage[]>(`/companies/${companyId}/messages`);
}

export async function sendMessage(
  companyId: string,
  req: SendMessageRequest
): Promise<ApiResponse<AgentMessage>> {
  return fetchApi<AgentMessage>(`/companies/${companyId}/messages`, {
    method: "POST",
    body: JSON.stringify(req),
  });
}
