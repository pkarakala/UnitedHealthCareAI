"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { Spinner, ErrorBanner } from "@/components/ui";
import { api } from "@/lib/api";
import type { Appeal } from "@/lib/types";
import { Scale } from "lucide-react";

export default function AppealsPage() {
  const [appeals, setAppeals] = useState<Appeal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const data = await api.appeals.list();
      setAppeals(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load appeals");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <>
      <Header title="Appeals" />
      <div className="p-6">
        {error && <ErrorBanner message={error} onRetry={load} />}

        <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden mt-4">
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-slate-50/50">
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Appeal #</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Level</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Status</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Denial Reason</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Decision</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {loading ? (
                  <tr><td colSpan={6}><Spinner label="Loading..." /></td></tr>
                ) : appeals.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-16 text-center">
                      <div className="flex flex-col items-center">
                        <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-3">
                          <Scale className="w-6 h-6 text-slate-300" />
                        </div>
                        <p className="text-sm font-medium text-slate-500">No appeals yet</p>
                        <p className="text-[12px] text-slate-500 mt-1">Appeals are created when a PA is denied</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  appeals.map((a) => (
                    <tr key={a.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-5 py-3 font-mono text-[12px] text-teal-600">
                        {a.appeal_number || a.id.slice(0, 8)}
                      </td>
                      <td className="px-5 py-3 text-slate-700">Level {a.level}</td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium ring-1 ring-inset ${
                          a.status === "approved" || a.status === "won"
                            ? "bg-teal-50 text-teal-700 ring-teal-200"
                            : a.status === "denied"
                            ? "bg-red-50 text-red-600 ring-red-200"
                            : "bg-amber-50 text-amber-700 ring-amber-200"
                        }`}>
                          {a.status}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-slate-600 max-w-xs truncate">{a.denial_reason || "—"}</td>
                      <td className="px-5 py-3 text-slate-700 font-medium">{a.decision || "Pending"}</td>
                      <td className="px-5 py-3 text-slate-500 text-[12px]">{new Date(a.created_at).toLocaleDateString()}</td>
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
