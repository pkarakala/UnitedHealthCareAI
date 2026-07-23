"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { StatCard, Spinner, ErrorBanner } from "@/components/ui";
import { api } from "@/lib/api";
import type { DashboardMetrics, AgentPerformanceMetrics } from "@/lib/types";

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [agentMetrics, setAgentMetrics] = useState<AgentPerformanceMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const [m, agents] = await Promise.all([
        api.analytics.dashboard(),
        api.analytics.agentPerformance(),
      ]);
      setMetrics(m);
      setAgentMetrics(agents);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  if (loading) {
    return (
      <>
        <Header title="Analytics" />
        <Spinner label="Loading analytics..." />
      </>
    );
  }

  return (
    <>
      <Header title="Analytics & Revenue" />
      <div className="p-6 space-y-6 max-w-[1400px]">
        {error && <ErrorBanner message={error} onRetry={load} />}

        {/* Revenue Section */}
        <div>
          <h3 className="text-[13px] font-semibold text-slate-900 mb-3">Revenue & Performance</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard title="Revenue Recovered (MTD)" value={`$${(metrics?.revenue_recovered_mtd ?? 0).toLocaleString()}`} />
            <StatCard title="Approval Rate" value={`${(metrics?.approval_rate ?? 0).toFixed(1)}%`} />
            <StatCard title="Appeal Success" value={`${(metrics?.appeal_success_rate ?? 0).toFixed(0)}%`} />
            <StatCard title="Avg Turnaround" value={`${(metrics?.average_turnaround_hours ?? 0).toFixed(0)}h`} />
          </div>
        </div>

        {/* Top Rejected Drugs */}
        {metrics?.top_rejected_drugs && metrics.top_rejected_drugs.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200/80 p-5">
            <h3 className="text-[13px] font-semibold text-slate-900 mb-4">Top Rejected Drugs</h3>
            <div className="space-y-2">
              {metrics.top_rejected_drugs.map((drug, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
                  <span className="text-[13px] text-slate-700">{drug.drug}</span>
                  <span className="text-[13px] font-medium text-red-600">{drug.count} denials</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Agent Performance */}
        <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100">
            <h3 className="text-[13px] font-semibold text-slate-900">Agent Performance</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-slate-50/50">
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Agent</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Executions</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Success Rate</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Avg Duration</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Tokens Used</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {agentMetrics.length === 0 ? (
                  <tr><td colSpan={5} className="px-5 py-12 text-center text-[13px] text-slate-400">No agent data yet.</td></tr>
                ) : (
                  agentMetrics.map((a) => (
                    <tr key={a.agent_name} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-5 py-3 font-medium text-slate-900">
                        {a.agent_name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
                      </td>
                      <td className="px-5 py-3 text-slate-600">{a.total_executions}</td>
                      <td className="px-5 py-3">
                        <span className={`font-medium ${
                          a.success_rate >= 90 ? "text-teal-600" :
                          a.success_rate >= 70 ? "text-amber-600" :
                          "text-red-600"
                        }`}>
                          {a.success_rate.toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-5 py-3 text-slate-600">{a.average_duration_ms.toFixed(0)}ms</td>
                      <td className="px-5 py-3 text-slate-600">{a.total_tokens_used.toLocaleString()}</td>
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
