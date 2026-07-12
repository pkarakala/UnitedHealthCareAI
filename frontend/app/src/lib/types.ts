/**
 * Prior Authorization AI Platform — TypeScript Types
 * Auto-generated from backend Pydantic schemas.
 * Drop this into your Next.js project for full type safety.
 */

// ─── Enums ────────────────────────────────────────────────────────────────────

export type PAStatus =
  | "intake"
  | "pa_detection"
  | "no_pa_required"
  | "insurance_verification"
  | "clinical_review"
  | "awaiting_records"
  | "doctor_outreach"
  | "followup_pending"
  | "form_filling"
  | "clinical_writing"
  | "ready_to_submit"
  | "submitted"
  | "pending_review"
  | "approved"
  | "denied"
  | "appeal_in_progress"
  | "appeal_submitted"
  | "appeal_approved"
  | "appeal_denied"
  | "completed"
  | "cancelled"
  | "error";

export type AgentType =
  | "prescription_intake"
  | "pa_detection"
  | "insurance_verification"
  | "clinical_requirement"
  | "patient_record"
  | "doctor_communication"
  | "followup"
  | "pa_form_filling"
  | "clinical_writing"
  | "submission"
  | "status_monitoring"
  | "approval"
  | "denial_analysis"
  | "appeal"
  | "patient_communication"
  | "revenue_analytics";

export type CommunicationChannel = "fax" | "email" | "sms" | "phone" | "portal";
export type CommunicationStatus = "pending" | "sent" | "delivered" | "failed" | "read";
export type DocumentType =
  | "prescription_image"
  | "lab_result"
  | "clinical_note"
  | "medical_necessity_letter"
  | "appeal_letter"
  | "denial_letter"
  | "insurance_card"
  | "progress_note";

// ─── Patient ──────────────────────────────────────────────────────────────────

export interface PatientCreate {
  first_name: string;
  last_name: string;
  date_of_birth: string; // ISO date "YYYY-MM-DD"
  phone?: string | null;
  email?: string | null;
  address?: Record<string, string> | null;
  member_id?: string | null;
  group_number?: string | null;
  insurance_id?: string | null;
}

export interface PatientUpdate {
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: Record<string, string> | null;
  member_id?: string | null;
  group_number?: string | null;
  insurance_id?: string | null;
}

export interface Patient extends PatientCreate {
  id: string;
  created_at: string;
  updated_at: string | null;
}

// ─── Prescription ─────────────────────────────────────────────────────────────

export interface PrescriptionCreate {
  patient_id: string;
  prescriber_npi: string;
  prescriber_name?: string | null;
  prescriber_phone?: string | null;
  prescriber_fax?: string | null;
  drug_name: string;
  ndc?: string | null;
  strength?: string | null;
  quantity?: number | null;
  days_supply?: number | null;
  refills?: number | null;
  directions?: string | null;
  diagnosis_codes?: string[] | null;
  pharmacy_npi?: string | null;
  date_written?: string | null;
  source?: string | null;
}

export interface Prescription extends PrescriptionCreate {
  id: string;
  raw_image_url: string | null;
  ocr_confidence: number | null;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface IntakeResponse {
  prescription_id: string;
  prior_auth_id: string;
  status: string;
  message: string;
}

// ─── Prior Authorization ──────────────────────────────────────────────────────

export interface PriorAuthCreate {
  patient_id: string;
  prescription_id: string;
  insurance_id?: string | null;
  priority?: number;
  notes?: string | null;
}

export interface PriorAuthUpdate {
  status?: string | null;
  sub_status?: string | null;
  pa_number?: string | null;
  submission_method?: string | null;
  decision?: string | null;
  denial_reason?: string | null;
  notes?: string | null;
  assigned_to?: string | null;
  priority?: number | null;
}

export interface PriorAuth {
  id: string;
  patient_id: string;
  prescription_id: string;
  insurance_id: string | null;
  status: PAStatus;
  sub_status: string | null;
  pa_number: string | null;
  confirmation_number: string | null;
  submission_method: string | null;
  submitted_at: string | null;
  decision_at: string | null;
  decision: string | null;
  denial_reason: string | null;
  medical_necessity_letter: string | null;
  clinical_summary: string | null;
  required_documents: Record<string, unknown> | null;
  collected_documents: Record<string, unknown> | null;
  claim_amount: number | null;
  revenue_recovered: number | null;
  current_agent: string | null;
  retry_count: number;
  escalated: boolean;
  assigned_to: string | null;
  priority: number;
  notes: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface TimelineEvent {
  timestamp: string;
  agent_name: string | null;
  action: string;
  status: string;
  details: Record<string, unknown> | null;
  duration_ms: number | null;
}

export interface PriorAuthTimeline {
  prior_auth_id: string;
  current_status: PAStatus;
  events: TimelineEvent[];
  total_duration_hours: number | null;
}

// ─── Insurance ────────────────────────────────────────────────────────────────

export interface InsuranceCreate {
  plan_name: string;
  payer_name?: string | null;
  bin_number?: string | null;
  pcn?: string | null;
  group_number?: string | null;
  phone?: string | null;
  fax?: string | null;
  portal_url?: string | null;
  formulary_data?: Record<string, unknown> | null;
  pa_requirements?: Record<string, unknown> | null;
  step_therapy_rules?: Record<string, unknown> | null;
  quantity_limits?: Record<string, unknown> | null;
}

export interface Insurance {
  id: string;
  plan_name: string;
  payer_name: string | null;
  bin_number: string | null;
  pcn: string | null;
  group_number: string | null;
  phone: string | null;
  fax: string | null;
  portal_url: string | null;
  is_active: boolean;
  formulary_data: Record<string, unknown> | null;
  pa_requirements: Record<string, unknown> | null;
  created_at: string;
}

export interface InsuranceVerificationRequest {
  member_id: string;
  bin_number?: string | null;
  pcn?: string | null;
  group_number?: string | null;
  patient_dob?: string | null;
}

export interface InsuranceVerificationResult {
  is_active: boolean;
  plan_name: string | null;
  coverage_type: string | null;
  copay: number | null;
  deductible_remaining: number | null;
  preferred_pharmacy: boolean | null;
  step_therapy_required: boolean;
  quantity_limit_applies: boolean;
  age_restriction: boolean;
  diagnosis_restriction: boolean;
  notes: string | null;
}

// ─── Communication ────────────────────────────────────────────────────────────

export interface Communication {
  id: string;
  prior_auth_id: string;
  channel: CommunicationChannel;
  direction: string;
  recipient: string;
  subject: string | null;
  body: string | null;
  status: CommunicationStatus;
  sent_at: string | null;
  delivered_at: string | null;
  error_message: string | null;
  created_at: string;
}

// ─── Appeal ───────────────────────────────────────────────────────────────────

export interface AppealCreate {
  prior_auth_id: string;
  level?: number;
  denial_reason?: string | null;
  denial_codes?: Record<string, unknown> | null;
}

export interface Appeal {
  id: string;
  prior_auth_id: string;
  appeal_number: string | null;
  level: number;
  status: string;
  denial_reason: string | null;
  appeal_strategy: string | null;
  appeal_letter: string | null;
  supporting_evidence: Record<string, unknown> | null;
  clinical_references: Record<string, unknown> | null;
  submitted_at: string | null;
  decision_at: string | null;
  decision: string | null;
  decision_notes: string | null;
  created_at: string;
}

export interface DenialAnalysis {
  prior_auth_id: string;
  denial_reason: string;
  denial_category: string;
  missing_items: string[];
  root_cause: string;
  is_appealable: boolean;
  appeal_success_probability: number | null;
  recommended_strategy: string;
  additional_evidence_needed: string[];
  suggested_alternatives: string[];
}

// ─── Analytics ────────────────────────────────────────────────────────────────

export interface DashboardMetrics {
  total_pas: number;
  pending_pas: number;
  approved_today: number;
  denied_today: number;
  average_turnaround_hours: number;
  approval_rate: number;
  appeal_success_rate: number;
  revenue_recovered_mtd: number;
  top_rejected_drugs: Array<{ drug: string; count: number }>;
  top_slow_insurers: Array<{ insurer: string; avg_hours: number }>;
  top_slow_prescribers: Array<{ prescriber: string; avg_hours: number }>;
}

export interface AgentPerformanceMetrics {
  agent_name: AgentType;
  total_executions: number;
  success_rate: number;
  average_duration_ms: number;
  total_tokens_used: number;
  total_cost_usd: number;
  error_rate: number;
}

// ─── Agent Execution ──────────────────────────────────────────────────────────

export interface AgentExecution {
  id: string;
  prior_auth_id: string;
  agent_name: AgentType;
  status: string;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
  tokens_input: number | null;
  tokens_output: number | null;
  model_used: string | null;
  cost_usd: number | null;
  error_message: string | null;
}

export interface AgentTriggerResponse {
  success: boolean;
  agent: string;
  message: string | null;
  data: Record<string, unknown>;
  requires_human: boolean;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export interface HealthCheck {
  status: "healthy" | "degraded";
  version: string;
  timestamp: string;
  database: string;
  redis: string;
}

// ─── Document ─────────────────────────────────────────────────────────────────

export interface DocumentUploadResponse {
  document_id: string;
  file_name: string;
  status: string;
  message: string;
}

export interface DocumentInfo {
  id: string;
  prior_auth_id: string;
  document_type: DocumentType;
  file_name: string;
  file_size: number | null;
  created_at: string;
}
