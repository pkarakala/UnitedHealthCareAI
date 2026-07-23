"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Header from "@/components/layout/Header";
import StatusBadge from "@/components/ui/StatusBadge";
import { api } from "@/lib/api";
import type { PriorAuth } from "@/lib/types";

export default function PriorAuthsPage() {
  const [priorAuths, setPriorAuths] = useState<PriorAuth[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const params: Record<string, string | number> = { limit: 50 };
        if (filter) params.status = filter;
        const data = await api.priorAuths.list(params);
        setPriorAuths(data);
      } catch (e) {
        console.error("Failed to load PAs:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [filter]);

  return (
    <>
      <Header title="Prior Authorizations" />
      <div className="p-6 space-y-4">
        {/* Filters */}
        <div className="flex gap-2 flex-wrap">
          {["", "pending_review", "submitted", "approved", "denied", "appeal_in_progress"].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                filter === s
                  ? "bg-emerald-600 text-white"
                  : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {s === "" ? "All" : s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">ID</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">Status</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">PA Number</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">Current Agent</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">Decision</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">Escalated</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-5 py-8 text-center text-slate-400">Loading...</td>
                  </tr>
                ) : priorAuths.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-5 py-8 text-center text-slate-400">
                      No prior authorizations found.
                    </td>
                  </tr>
                ) : (
                  priorAuths.map((pa) => (
                    <tr key={pa.id} className="hover:bg-slate-50">
                      <td className="px-5 py-3">
                        <Link href={`/prior-auths/${pa.id}`} className="text-emerald-600 hover:underline font-mono text-xs">
                          {pa.id.slice(0, 8)}
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
                        </div>
                      </td>
                      <td className="px-5 py-3 text-slate-600">{pa.pa_number || "—"}</td>
                      <td className="px-5 py-3 text-slate-600">{pa.current_agent?.replace(/_/g, " ") || "—"}</td>
                      <td className="px-5 py-3 text-slate-600">{pa.decision || "—"}</td>
                      <td className="px-5 py-3">{pa.escalated ? "⚠️ Yes" : "—"}</td>
                      <td className="px-5 py-3 text-slate-500">{new Date(pa.created_at).toLocaleString()}</td>
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
