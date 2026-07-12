"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Header from "@/components/layout/Header";
import StatusBadge from "@/components/ui/StatusBadge";
import { api } from "@/lib/api";
import type { PriorAuth, PriorAuthTimeline, TimelineEvent } from "@/lib/types";

export default function PriorAuthDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [pa, setPA] = useState<PriorAuth | null>(null);
  const [timeline, setTimeline] = useState<PriorAuthTimeline | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [paData, timelineData] = await Promise.all([
          api.priorAuths.get(id),
          api.priorAuths.timeline(id),
        ]);
        setPA(paData);
        setTimeline(timelineData);
      } catch (e) {
        console.error("Failed to load PA:", e);
      } finally {
        setLoading(false);
      }
    }
    if (id) load();
  }, [id]);

  if (loading) {
    return (
      <>
        <Header title="Prior Authorization Detail" />
        <div className="p-6 flex items-center justify-center h-64">
          <p className="text-slate-500">Loading...</p>
        </div>
      </>
    );
  }

  if (!pa) {
    return (
      <>
        <Header title="Prior Authorization Detail" />
        <div className="p-6">
          <p className="text-red-500">Prior authorization not found.</p>
        </div>
      </>
    );
  }

  return (
    <>
      <Header title={`PA: ${pa.pa_number || pa.id.slice(0, 8)}`} />
      <div className="p-6 space-y-6">
        {/* Status Header */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <StatusBadge status={pa.status} />
                {pa.escalated && (
                  <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Escalated</span>
                )}
              </div>
              <p className="mt-2 text-sm text-slate-600">
                PA Number: <span className="font-mono">{pa.pa_number || "Not assigned"}</span>
              </p>
              <p className="text-sm text-slate-600">
                Confirmation: <span className="font-mono">{pa.confirmation_number || "—"}</span>
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={async () => {
                  await api.priorAuths.advance(id, "approved");
                  window.location.reload();
                }}
                className="px-4 py-2 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700"
              >
                Mark Approved
              </button>
              <button
                onClick={async () => {
                  await api.priorAuths.escalate(id);
                  window.location.reload();
                }}
                className="px-4 py-2 bg-amber-500 text-white text-sm rounded-lg hover:bg-amber-600"
              >
                Escalate
              </button>
              <button
                onClick={async () => {
                  await api.priorAuths.cancel(id);
                  window.location.reload();
                }}
                className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* PA Info */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="font-semibold text-slate-900 mb-4">PA Details</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Submission Method</dt>
                <dd className="text-slate-900">{pa.submission_method || "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Decision</dt>
                <dd className="text-slate-900 font-medium">{pa.decision || "Pending"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Submitted</dt>
                <dd className="text-slate-900">{pa.submitted_at ? new Date(pa.submitted_at).toLocaleString() : "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Decision Date</dt>
                <dd className="text-slate-900">{pa.decision_at ? new Date(pa.decision_at).toLocaleString() : "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Priority</dt>
                <dd className="text-slate-900">{pa.priority}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Revenue Recovered</dt>
                <dd className="text-emerald-600 font-medium">{pa.revenue_recovered ? `$${pa.revenue_recovered}` : "—"}</dd>
              </div>
            </dl>
          </div>

          {/* Clinical Info */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Clinical Information</h3>
            {pa.clinical_summary ? (
              <p className="text-sm text-slate-700">{pa.clinical_summary}</p>
            ) : (
              <p className="text-sm text-slate-400">No clinical summary yet.</p>
            )}
            {pa.denial_reason && (
              <div className="mt-4 p-3 bg-red-50 rounded-lg">
                <p className="text-sm font-medium text-red-700">Denial Reason:</p>
                <p className="text-sm text-red-600 mt-1">{pa.denial_reason}</p>
              </div>
            )}
          </div>
        </div>

        {/* Medical Necessity Letter */}
        {pa.medical_necessity_letter && (
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Medical Necessity Letter</h3>
            <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans leading-relaxed">
              {pa.medical_necessity_letter}
            </pre>
          </div>
        )}

        {/* Agent Timeline */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="font-semibold text-slate-900 mb-4">
            Agent Execution Timeline
            {timeline?.total_duration_hours && (
              <span className="ml-2 text-sm font-normal text-slate-500">
                ({timeline.total_duration_hours.toFixed(1)} hours total)
              </span>
            )}
          </h3>
          <div className="space-y-3">
            {timeline?.events.length === 0 ? (
              <p className="text-sm text-slate-400">No agent executions yet.</p>
            ) : (
              timeline?.events.map((event, i) => (
                <div key={i} className="flex items-start gap-3 pb-3 border-b border-slate-100 last:border-0">
                  <div className={`w-2 h-2 rounded-full mt-2 ${
                    event.status === "completed" ? "bg-emerald-500" :
                    event.status === "error" ? "bg-red-500" :
                    "bg-amber-500"
                  }`} />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-slate-900">
                        {event.agent_name?.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
                      </p>
                      <span className="text-xs text-slate-400">
                        {event.duration_ms ? `${event.duration_ms}ms` : ""}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
}
