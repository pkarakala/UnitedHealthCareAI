const statusConfig: Record<string, { label: string; color: string }> = {
  intake: { label: "Intake", color: "bg-slate-50 text-slate-600 ring-slate-200" },
  pa_detection: { label: "Detecting", color: "bg-blue-50 text-blue-600 ring-blue-200" },
  no_pa_required: { label: "No PA Needed", color: "bg-emerald-50 text-emerald-600 ring-emerald-200" },
  insurance_verification: { label: "Verifying", color: "bg-indigo-50 text-indigo-600 ring-indigo-200" },
  clinical_review: { label: "Clinical Review", color: "bg-purple-50 text-purple-600 ring-purple-200" },
  awaiting_records: { label: "Awaiting Records", color: "bg-amber-50 text-amber-600 ring-amber-200" },
  doctor_outreach: { label: "Doctor Outreach", color: "bg-orange-50 text-orange-600 ring-orange-200" },
  followup_pending: { label: "Follow-up", color: "bg-amber-50 text-amber-600 ring-amber-200" },
  form_filling: { label: "Filling Form", color: "bg-blue-50 text-blue-600 ring-blue-200" },
  clinical_writing: { label: "Writing Letter", color: "bg-purple-50 text-purple-600 ring-purple-200" },
  ready_to_submit: { label: "Ready", color: "bg-indigo-50 text-indigo-600 ring-indigo-200" },
  submitted: { label: "Submitted", color: "bg-indigo-50 text-indigo-600 ring-indigo-200" },
  pending_review: { label: "Pending Review", color: "bg-yellow-50 text-yellow-700 ring-yellow-200" },
  approved: { label: "Approved", color: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  denied: { label: "Denied", color: "bg-red-50 text-red-600 ring-red-200" },
  appeal_in_progress: { label: "Appealing", color: "bg-orange-50 text-orange-600 ring-orange-200" },
  appeal_submitted: { label: "Appeal Sent", color: "bg-orange-50 text-orange-600 ring-orange-200" },
  appeal_approved: { label: "Appeal Won", color: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  appeal_denied: { label: "Appeal Denied", color: "bg-red-50 text-red-600 ring-red-200" },
  completed: { label: "Completed", color: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  cancelled: { label: "Cancelled", color: "bg-slate-50 text-slate-500 ring-slate-200" },
  error: { label: "Error", color: "bg-red-50 text-red-600 ring-red-200" },
};

export default function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] || { label: status, color: "bg-slate-50 text-slate-600 ring-slate-200" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium ring-1 ring-inset ${config.color}`}>
      {config.label}
    </span>
  );
}
