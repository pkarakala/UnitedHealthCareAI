import type { PAStatus } from "@/lib/types";

const statusConfig: Record<string, { label: string; color: string }> = {
  intake: { label: "Intake", color: "bg-slate-100 text-slate-700" },
  pa_detection: { label: "Detecting", color: "bg-blue-100 text-blue-700" },
  no_pa_required: { label: "No PA Needed", color: "bg-green-100 text-green-700" },
  insurance_verification: { label: "Verifying Insurance", color: "bg-blue-100 text-blue-700" },
  clinical_review: { label: "Clinical Review", color: "bg-purple-100 text-purple-700" },
  awaiting_records: { label: "Awaiting Records", color: "bg-amber-100 text-amber-700" },
  doctor_outreach: { label: "Doctor Outreach", color: "bg-amber-100 text-amber-700" },
  followup_pending: { label: "Follow-up", color: "bg-amber-100 text-amber-700" },
  form_filling: { label: "Filling Form", color: "bg-blue-100 text-blue-700" },
  clinical_writing: { label: "Writing Letter", color: "bg-purple-100 text-purple-700" },
  ready_to_submit: { label: "Ready to Submit", color: "bg-indigo-100 text-indigo-700" },
  submitted: { label: "Submitted", color: "bg-indigo-100 text-indigo-700" },
  pending_review: { label: "Pending Review", color: "bg-yellow-100 text-yellow-700" },
  approved: { label: "Approved", color: "bg-emerald-100 text-emerald-700" },
  denied: { label: "Denied", color: "bg-red-100 text-red-700" },
  appeal_in_progress: { label: "Appealing", color: "bg-orange-100 text-orange-700" },
  appeal_submitted: { label: "Appeal Submitted", color: "bg-orange-100 text-orange-700" },
  appeal_approved: { label: "Appeal Won", color: "bg-emerald-100 text-emerald-700" },
  appeal_denied: { label: "Appeal Denied", color: "bg-red-100 text-red-700" },
  completed: { label: "Completed", color: "bg-emerald-100 text-emerald-700" },
  cancelled: { label: "Cancelled", color: "bg-slate-100 text-slate-500" },
  error: { label: "Error", color: "bg-red-100 text-red-700" },
};

export default function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] || { label: status, color: "bg-slate-100 text-slate-700" };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
      {config.label}
    </span>
  );
}
