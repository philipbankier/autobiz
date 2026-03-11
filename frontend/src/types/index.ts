// === Enums ===

export enum CompanyStatus {
  PENDING = "pending",
  ACTIVE = "active",
  PAUSED = "paused",
  SUSPENDED = "suspended",
}

export enum DepartmentType {
  MARKETING = "marketing",
  SALES = "sales",
  CUSTOMER_SUPPORT = "customer_support",
  PRODUCT = "product",
  ENGINEERING = "engineering",
  FINANCE = "finance",
  HR = "hr",
  OPERATIONS = "operations",
  RESEARCH = "research",
  LEGAL = "legal",
}

export enum AutonomyLevel {
  FULL = "full",
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
  MANUAL = "manual",
}

export enum DepartmentStatus {
  ACTIVE = "active",
  PAUSED = "paused",
  DISABLED = "disabled",
}

export enum TaskStatus {
  TODO = "todo",
  IN_PROGRESS = "in_progress",
  DONE = "done",
  BLOCKED = "blocked",
}

export enum TaskPriority {
  CRITICAL = "critical",
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
}

export enum AgentRunStatus {
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
  SYSTEM = "system",
}

// === Models ===

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  mission: string;
  status: CompanyStatus;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  company_id: string;
  type: DepartmentType;
  autonomy_level: AutonomyLevel;
  status: DepartmentStatus;
  budget_cap: number | null;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AgentRun {
  id: string;
  company_id: string;
  department_type: DepartmentType;
  status: AgentRunStatus;
  summary: string | null;
  tokens_used: number;
  cost_usd: number;
  started_at: string;
  completed_at: string | null;
  error: string | null;
}

export interface AgentTask {
  id: string;
  company_id: string;
  department_type: DepartmentType;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_agent: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface AgentMessage {
  id: string;
  company_id: string;
  department_type: DepartmentType | null;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface CostEvent {
  id: string;
  company_id: string;
  department_type: DepartmentType;
  event_type: string;
  amount_usd: number;
  description: string;
  created_at: string;
}

// === API Response ===

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  meta: Record<string, unknown> | null;
}

// === Auth ===

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// === Create/Update ===

export interface CreateCompanyRequest {
  name: string;
  slug: string;
  mission: string;
}

export interface CreateTaskRequest {
  title: string;
  description: string;
  department_type: DepartmentType;
  priority: TaskPriority;
}

export interface UpdateDepartmentRequest {
  autonomy_level?: AutonomyLevel;
  budget_cap?: number | null;
  status?: DepartmentStatus;
}

export interface SendMessageRequest {
  content: string;
  department_type?: DepartmentType;
}
