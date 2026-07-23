"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import { StatusBadge, PriorityBadge, Spinner, ErrorBanner } from "@/components/ui";
import { api } from "@/lib/api";
import type { PriorAuth } from "@/lib/types";
import { ClipboardList, AlertTriangle } from "lucide-react";

const STATUS_FILTERS = [
  "",
  "pending_review",
  "submitted",
  "approved",
  "denied",
  "appeal_in_progress",
  "awaiting_records",
  "escalated",
] as const;

export default function PriorAuthsPage() {
  const [priorAuths, setPriorAuths] = useState<PriorAuth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const params: Record<string, string | number | boolean> = { limit: 50 };
      if (filter === "escalated") {
        params.escalated = true;
      } else if (filter) {
        params.status = filter;
      }
      const data = await api.priorAuths.list(params);
      setPriorAuths(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load prior authorizations");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filter]);

  return (
    <>
      <Header title="Prior Authorizations" />
      <div className="p-6 space-y-4">
        {error && <ErrorBanner message={error} onRetry={load} />}

        {/* Filters */}
        <div className="flex gap-2 flex-wrap">
          {STATUS_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-[12px] font-medium transition-colors ${
                filter === s
                  ? "bg-teal-600 text-white"
                  : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {s === "" ? "All" : s === "escalated" ? "Escalated" : s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-slate-50/50">
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Case</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Status</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Agent</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Priority</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Decision</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Age</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {loading ? (
                  <tr>
                    <td colSpan={6}><Spinner label="Loading..." /></td>
                  </tr>
                ) : priorAuths.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-16 text-center">
                      <div className="flex flex-col items-center">
                        <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-3">
                          <ClipboardList className="w-6 h-6 text-slate-300" />
                        </div>
                        <p className="text-sm font-medium text-slate-500">No prior authorizations found</p>
                        <p className="text-[12px] text-slate-400 mt-1">
                          {filter ? "Try a different filter" : "Start by intaking a new prescription"}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  priorAuths.map((pa) => (
                    <tr key={pa.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-5 py-3">
                        <Link href={`/prior-auths/${pa.id}`} className="text-teal-600 hover:underline font-mono text-[12px]">
                          {pa.pa_number || pa.id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-1.5">
                          <StatusBadge status={pa.status} />
                          {pa.is_simulated && (
                            <span className="text-[10px] uppercase tracking-wide bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded" title="Contains simulated data">
                              Sim
                            </span>
                          )}
                          {pa.escalated && (
                            <span title="Escalated"><AlertTriangle className="w-3.5 h-3.5 text-red-500" /></span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-3 text-slate-600">
                        {pa.current_agent?.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) || "—"}
                      </td>
                      <td className="px-5 py-3">
                        <PriorityBadge priority={pa.priority} />
                      </td>
                      <td className="px-5 py-3 text-slate-600">{pa.decision || "—"}</td>
                      <td className="px-5 py-3 text-slate-400 text-[12px]">{formatAge(pa.created_at)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}

function formatAge(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 3_600_000);
  if (hours < 1) return "< 1h";
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  return `${days}d`;
}
