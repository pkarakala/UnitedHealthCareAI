/**
 * Prior Authorization AI Platform — API Client
 * Typed fetch-based client for the PA backend.
 *
 * Usage:
 *   import { PAClient } from './client';
 *   const api = new PAClient('http://localhost:8000');
 *   const patients = await api.patients.list();
 */

import type {
  Patient,
  PatientCreate,
  PatientUpdate,
  Prescription,
  PrescriptionCreate,
  IntakeResponse,
  PriorAuth,
  PriorAuthCreate,
  PriorAuthUpdate,
  PriorAuthTimeline,
  Insurance,
  InsuranceCreate,
  InsuranceVerificationRequest,
  InsuranceVerificationResult,
  Communication,
  Appeal,
  AppealCreate,
  DashboardMetrics,
  AgentPerformanceMetrics,
  AgentExecution,
  AgentTriggerResponse,
  HealthCheck,
  DocumentInfo,
  DocumentUploadResponse,
} from "./types";

// ─── Configuration ────────────────────────────────────────────────────────────

interface ClientConfig {
  baseUrl: string;
  /** Called per-request so tokens set after module init are picked up. */
  getToken?: () => string | null;
  onUnauthorized?: () => void;
}

// ─── Core Fetch Wrapper ───────────────────────────────────────────────────────

class ApiBase {
  private baseUrl: string;
  private getToken?: () => string | null;
  private onUnauthorized?: () => void;

  constructor(config: ClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.getToken = config.getToken;
    this.onUnauthorized = config.onUnauthorized;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    options?: { params?: Record<string, string | number | boolean | undefined> }
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}/api/v1${path}`);

    if (options?.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.set(key, String(value));
        }
      });
    }

    const headers: Record<string, string> = {};
    const token = this.getToken?.();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    if (body && !(body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    const response = await fetch(url.toString(), {
      method,
      headers,
      body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    });

    if (response.status === 401) {
      this.onUnauthorized?.();
      throw new ApiError(401, "Unauthorized");
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new ApiError(response.status, error.detail || "Request failed");
    }

    return response.json();
  }

  protected get<T>(path: string, params?: Record<string, string | number | boolean | undefined>) {
    return this.request<T>("GET", path, undefined, { params });
  }

  protected post<T>(path: string, body?: unknown) {
    return this.request<T>("POST", path, body);
  }

  protected put<T>(path: string, body?: unknown) {
    return this.request<T>("PUT", path, body);
  }

  protected postForm<T>(path: string, formData: FormData) {
    return this.request<T>("POST", path, formData);
  }
}

// ─── Error Class ──────────────────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

// ─── API Client ───────────────────────────────────────────────────────────────

export class PAClient extends ApiBase {
  // ── Health ──────────────────────────────────────────────────────────────

  health = {
    check: () => this.get<HealthCheck>("/health"),
    ready: () => this.get<{ ready: boolean }>("/health/ready"),
  };

  // ── Auth ────────────────────────────────────────────────────────────────

  auth = {
    login: (email: string, password: string) =>
      this.post<{ access_token: string; token_type: string }>("/auth/login", {
        email,
        password,
      }),

    me: () =>
      this.get<{ id: string; email: string; full_name: string | null; role: string }>(
        "/auth/me"
      ),
  };

  // ── Patients ────────────────────────────────────────────────────────────

  patients = {
    list: (params?: { skip?: number; limit?: number; search?: string }) =>
      this.get<Patient[]>("/patients", params),

    get: (id: string) => this.get<Patient>(`/patients/${id}`),

    create: (data: PatientCreate) => this.post<Patient>("/patients", data),

    update: (id: string, data: PatientUpdate) =>
      this.put<Patient>(`/patients/${id}`, data),

    getPriorAuths: (id: string) =>
      this.get<PriorAuth[]>(`/patients/${id}/prior-auths`),
  };

  // ── Prescriptions ──────────────────────────────────────────────────────

  prescriptions = {
    list: (params?: { skip?: number; limit?: number; status?: string; patient_id?: string }) =>
      this.get<Prescription[]>("/prescriptions", params),

    get: (id: string) => this.get<Prescription>(`/prescriptions/${id}`),

    create: (data: PrescriptionCreate) =>
      this.post<Prescription>("/prescriptions", data),

    intake: (data: {
      patient_id: string;
      prescriber_npi: string;
      drug_name: string;
      prescriber_name?: string;
      prescriber_phone?: string;
      prescriber_fax?: string;
      strength?: string;
      quantity?: number;
      days_supply?: number;
      directions?: string;
      ndc?: string;
      insurance_id?: string;
      image?: File;
    }) => {
      const form = new FormData();
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (value instanceof File) {
            form.append(key, value);
          } else {
            form.append(key, String(value));
          }
        }
      });
      return this.postForm<IntakeResponse>("/prescriptions/intake", form);
    },
  };

  // ── Prior Authorizations ───────────────────────────────────────────────

  priorAuths = {
    list: (params?: {
      skip?: number;
      limit?: number;
      status?: string;
      patient_id?: string;
      escalated?: boolean;
    }) => this.get<PriorAuth[]>("/prior-auths", params),

    get: (id: string) => this.get<PriorAuth>(`/prior-auths/${id}`),

    create: (data: PriorAuthCreate) => this.post<PriorAuth>("/prior-auths", data),

    update: (id: string, data: PriorAuthUpdate) =>
      this.put<PriorAuth>(`/prior-auths/${id}`, data),

    timeline: (id: string) =>
      this.get<PriorAuthTimeline>(`/prior-auths/${id}/timeline`),

    triggerAgent: (id: string, agentName: string, force = false) =>
      this.post<AgentTriggerResponse>(
        `/prior-auths/${id}/trigger/${agentName}?force=${force}`
      ),

    advance: (id: string, condition?: string) =>
      this.post<{ success: boolean; message: string; new_status: string }>(
        `/prior-auths/${id}/advance${condition ? `?condition=${condition}` : ""}`
      ),

    cancel: (id: string) =>
      this.post<{ message: string; id: string }>(`/prior-auths/${id}/cancel`),

    escalate: (id: string, assignedTo?: string) =>
      this.post<{ message: string; id: string; assigned_to: string | null }>(
        `/prior-auths/${id}/escalate${assignedTo ? `?assigned_to=${assignedTo}` : ""}`
      ),
  };

  // ── Insurance ──────────────────────────────────────────────────────────

  insurance = {
    verify: (data: InsuranceVerificationRequest) =>
      this.post<InsuranceVerificationResult>("/insurance/verify", data),

    listPlans: (params?: { skip?: number; limit?: number }) =>
      this.get<Insurance[]>("/insurance/plans", params),

    createPlan: (data: InsuranceCreate) =>
      this.post<Insurance>("/insurance/plans", data),

    getPlan: (id: string) => this.get<Insurance>(`/insurance/plans/${id}`),
  };

  // ── Communications ─────────────────────────────────────────────────────

  communications = {
    list: (params?: {
      skip?: number;
      limit?: number;
      prior_auth_id?: string;
      channel?: string;
      status?: string;
    }) => this.get<Communication[]>("/communications", params),

    get: (id: string) => this.get<Communication>(`/communications/${id}`),

    resend: (id: string) =>
      this.post<{ message: string; id: string }>(`/communications/${id}/resend`),
  };

  // ── Appeals ────────────────────────────────────────────────────────────

  appeals = {
    list: (params?: { skip?: number; limit?: number; prior_auth_id?: string; status?: string }) =>
      this.get<Appeal[]>("/appeals", params),

    get: (id: string) => this.get<Appeal>(`/appeals/${id}`),

    create: (data: AppealCreate) => this.post<Appeal>("/appeals", data),
  };

  // ── Analytics ──────────────────────────────────────────────────────────

  analytics = {
    dashboard: () => this.get<DashboardMetrics>("/analytics/dashboard"),

    revenue: () =>
      this.get<{ total_claims_submitted: number; total_recovered: number; recovery_rate: number }>(
        "/analytics/revenue"
      ),

    turnaround: () => this.get<Record<string, number | string>>("/analytics/turnaround"),

    agentPerformance: () =>
      this.get<AgentPerformanceMetrics[]>("/analytics/agent-performance"),
  };

  // ── Documents ──────────────────────────────────────────────────────────

  documents = {
    list: (params?: { prior_auth_id?: string; document_type?: string }) =>
      this.get<DocumentInfo[]>("/documents", params),

    upload: (priorAuthId: string, documentType: string, file: File) => {
      const form = new FormData();
      form.append("prior_auth_id", priorAuthId);
      form.append("document_type", documentType);
      form.append("file", file);
      return this.postForm<DocumentUploadResponse>("/documents/upload", form);
    },

    download: (id: string) =>
      this.get<{ document_id: string; file_name: string; file_path: string }>(
        `/documents/${id}/download`
      ),
  };

  // ── Agents ─────────────────────────────────────────────────────────────

  agents = {
    types: () =>
      this.get<{ agents: Array<{ name: string; description: string }> }>("/agents/types"),

    executions: (params?: {
      skip?: number;
      limit?: number;
      agent_name?: string;
      prior_auth_id?: string;
      status?: string;
    }) => this.get<AgentExecution[]>("/agents/executions", params),

    stats: () =>
      this.get<Array<{ agent_name: string; total_runs: number; avg_duration_ms: number }>>(
        "/agents/stats"
      ),
  };
}
