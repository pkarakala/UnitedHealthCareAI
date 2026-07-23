"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import { StatusBadge, Button, ConfirmDialog, Spinner, ErrorBanner } from "@/components/ui";
import { api } from "@/lib/api";
import type { PriorAuth, PriorAuthTimeline } from "@/lib/types";
import { CheckCircle2, AlertTriangle, XCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";

type ConfirmAction = "approve" | "escalate" | "cancel" | null;

export default function PriorAuthDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [pa, setPA] = useState<PriorAuth | null>(null);
  const [timeline, setTimeline] = useState<PriorAuthTimeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);
  const [actionLoading, setActionLoading] = useState(false);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [paData, timelineData] = await Promise.all([
        api.priorAuths.get(id),
        api.priorAuths.timeline(id),
      ]);
      setPA(paData);
      setTimeline(timelineData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load PA details");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { if (id) load(); }, [id]);

  async function executeAction() {
    if (!confirmAction) return;
    setActionLoading(true);
    try {
      if (confirmAction === "approve") await api.priorAuths.advance(id, "approved");
      else if (confirmAction === "escalate") await api.priorAuths.escalate(id);
      else if (confirmAction === "cancel") await api.priorAuths.cancel(id);
      setConfirmAction(null);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
      setConfirmAction(null);
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Prior Authorization Detail" />
        <Spinner label="Loading PA..." />
      </>
    );
  }

  if (error && !pa) {
    return (
      <>
        <Header title="Prior Authorization Detail" />
        <div className="p-6">
          <ErrorBanner message={error} onRetry={load} />
        </div>
      </>
    );
  }

  if (!pa) {
    return (
      <>
        <Header title="Prior Authorization Detail" />
        <div className="p-6">
          <ErrorBanner message="Prior authorization not found." />
        </div>
      </>
    );
  }

  const confirmConfig: Record<string, { title: string; description: string; label: string; variant: "danger" | "primary" }> = {
    approve: {
      title: "Approve this PA?",
      description: "This will advance the PA to approved status. Make sure the clinical review is complete before approving.",
      label: "Approve",
      variant: "primary",
    },
    escalate: {
      title: "Escalate this PA?",
      description: "This will flag the PA for manual review and assign it to a staff member. Use when automated processing cannot continue.",
      label: "Escalate",
      variant: "danger",
    },
    cancel: {
      title: "Cancel this PA?",
      description: "This action cannot be undone. The PA will be marked as cancelled and no further processing will occur.",
      label: "Cancel PA",
      variant: "danger",
    },
  };

  const activeConfirm = confirmAction ? confirmConfig[confirmAction] : null;

  return (
    <>
      <Header title={`PA: ${pa.pa_number || pa.id.slice(0, 8)}`} />
      <div className="p-6 space-y-6 max-w-[1100px]">
        {error && <ErrorBanner message={error} onRetry={load} />}

        {/* Back link */}
        <Link href="/prior-auths" className="inline-flex items-center gap-1.5 text-[12px] text-slate-500 hover:text-slate-700 transition-colors">
          <ArrowLeft className="w-3 h-3" /> Back to queue
        </Link>

        {/* Status Header */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-2.5">
                <StatusBadge status={pa.status} />
                {pa.escalated && (
                  <span className="text-[11px] bg-red-100 text-red-700 px-2 py-0.5 rounded font-medium">Escalated</span>
                )}
                {pa.is_simulated && (
                  <span
                    className="text-[11px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded"
                    title={`Simulated: ${(pa.simulated_agents || []).join(", ")}`}
                  >
                    Simulated data
                  </span>
                )}
              </div>
              <div className="mt-2 flex items-center gap-4 text-[13px] text-slate-500">
                <span>PA: <span className="font-mono text-slate-700">{pa.pa_number || "Not assigned"}</span></span>
                {pa.confirmation_number && (
                  <span>Conf: <span className="font-mono text-slate-700">{pa.confirmation_number}</span></span>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="primary"
                icon={<CheckCircle2 className="w-3.5 h-3.5" />}
                onClick={() => setConfirmAction("approve")}
              >
                Approve
              </Button>
              <Button
                size="sm"
                variant="secondary"
                icon={<AlertTriangle className="w-3.5 h-3.5" />}
                onClick={() => setConfirmAction("escalate")}
              >
                Escalate
              </Button>
              <Button
                size="sm"
                variant="danger"
                icon={<XCircle className="w-3.5 h-3.5" />}
                onClick={() => setConfirmAction("cancel")}
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div className="bg-white rounded-xl border border-slate-200/80 p-5">
            <h3 className="text-[13px] font-semibold text-slate-900 mb-4">PA Details</h3>
            <dl className="space-y-2.5 text-[13px]">
              {[
                ["Submission Method", pa.submission_method],
                ["Decision", pa.decision || "Pending"],
                ["Submitted", pa.submitted_at ? new Date(pa.submitted_at).toLocaleString() : null],
                ["Decision Date", pa.decision_at ? new Date(pa.decision_at).toLocaleString() : null],
                ["Priority", String(pa.priority)],
                ["Revenue Recovered", pa.revenue_recovered ? `$${pa.revenue_recovered}` : null],
              ].map(([label, value]) => (
                <div key={label as string} className="flex justify-between">
                  <dt className="text-slate-500">{label}</dt>
                  <dd className="text-slate-900 font-medium">{(value as string) || "—"}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="bg-white rounded-xl border border-slate-200/80 p-5">
            <h3 className="text-[13px] font-semibold text-slate-900 mb-4">Clinical Information</h3>
            {pa.clinical_summary ? (
              <p className="text-[13px] text-slate-700 leading-relaxed">{pa.clinical_summary}</p>
            ) : (
              <p className="text-[13px] text-slate-400">No clinical summary yet.</p>
            )}
            {pa.denial_reason && (
              <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-lg">
                <p className="text-[12px] font-medium text-red-700">Denial Reason</p>
                <p className="text-[13px] text-red-600 mt-1">{pa.denial_reason}</p>
              </div>
            )}
          </div>
        </div>

        {/* Medical Necessity Letter */}
        {pa.medical_necessity_letter && (
          <div className="bg-white rounded-xl border border-slate-200/80 p-5">
            <h3 className="text-[13px] font-semibold text-slate-900 mb-4">Medical Necessity Letter</h3>
            <pre className="text-[13px] text-slate-700 whitespace-pre-wrap font-sans leading-relaxed">
              {pa.medical_necessity_letter}
            </pre>
          </div>
        )}

        {/* Agent Timeline */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5">
          <h3 className="text-[13px] font-semibold text-slate-900 mb-4">
            Agent Timeline
            {timeline?.total_duration_hours != null && (
              <span className="ml-2 text-[12px] font-normal text-slate-400">
                {timeline.total_duration_hours.toFixed(1)}h total
              </span>
            )}
          </h3>
          <div className="space-y-2">
            {!timeline?.events.length ? (
              <p className="text-[13px] text-slate-400">No agent executions yet.</p>
            ) : (
              timeline.events.map((event, i) => (
                <div key={i} className="flex items-start gap-3 py-2 border-b border-slate-50 last:border-0">
                  <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                    event.status === "completed" ? "bg-teal-500" :
                    event.status === "error" ? "bg-red-500" :
                    "bg-amber-500"
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-[13px] font-medium text-slate-900 truncate">
                        {event.agent_name?.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
                      </p>
                      <span className="text-[11px] text-slate-400 shrink-0">
                        {event.duration_ms ? `${event.duration_ms}ms` : ""}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Confirm Dialog */}
      {activeConfirm && (
        <ConfirmDialog
          open={!!confirmAction}
          title={activeConfirm.title}
          description={activeConfirm.description}
          confirmLabel={activeConfirm.label}
          variant={activeConfirm.variant}
          loading={actionLoading}
          onConfirm={executeAction}
          onCancel={() => setConfirmAction(null)}
        />
      )}
    </>
  );
}
