from pydantic import BaseModel
from datetime import datetime


class DashboardMetrics(BaseModel):
    total_pas: int
    pending_pas: int
    approved_today: int
    denied_today: int
    average_turnaround_hours: float
    approval_rate: float
    appeal_success_rate: float
    revenue_recovered_mtd: float
    top_rejected_drugs: list[dict] = []
    top_slow_insurers: list[dict] = []
    top_slow_prescribers: list[dict] = []


class RevenueMetrics(BaseModel):
    period: str
    total_claims_submitted: float
    total_approved_amount: float
    total_denied_amount: float
    total_recovered_via_appeal: float
    net_revenue_recovered: float
    pa_completion_rate: float
    average_cost_per_pa: float


class AgentPerformanceMetrics(BaseModel):
    agent_name: str
    total_executions: int
    success_rate: float
    average_duration_ms: float
    total_tokens_used: int
    total_cost_usd: float
    error_rate: float


class TurnaroundMetrics(BaseModel):
    average_intake_to_submission_hours: float
    average_submission_to_decision_hours: float
    average_total_hours: float
    median_total_hours: float
    percentile_95_hours: float
    by_insurance: list[dict] = []
    by_drug: list[dict] = []
