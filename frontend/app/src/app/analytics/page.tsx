"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import StatCard from "@/components/ui/StatCard";
import { api } from "@/lib/api";
import type { DashboardMetrics, AgentPerformanceMetrics } from "@/lib/types";

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [agentMetrics, setAgentMetrics] = useState<AgentPerformanceMetrics[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [m, agents] = await Promise.all([
          api.analytics.dashboard(),
          api.analytics.agentPerformance(),
        ]);
        setMetrics(m);
        setAgentMetrics(agents);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <>
        <Header title="Analytics" />
        <div className="p-6 flex items-center justify-center h-64">
          <p className="text-slate-500">Loading analytics...</p>
        </div>
      </>
    );
  }

  return (
    <>
      <Header title="Analytics & Revenue" />
      <div className="p-6 space-y-6">
        {/* Revenue Section */}
        <div>
          <h3 className="text-sm font-semibold text-slate-900 mb-3">Revenue & Performance</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard title="Revenue Recovered (MTD)" value={`$${(metrics?.revenue_recovered_mtd ?? 0).toLocaleString()}`} color="emerald" />
            <StatCard title="Approval Rate" value={`${(metrics?.approval_rate ?? 0).toFixed(1)}%`} color="emerald" />
            <StatCard title="Appeal Success" value={`${(metrics?.appeal_success_rate ?? 0).toFixed(0)}%`} color="blue" />
            <StatCard title="Avg Turnaround" value={`${(metrics?.average_turnaround_hours ?? 0).toFixed(0)}h`} color="amber" />
          </div>
        </div>

        {/* Top Rejected Drugs */}
        {metrics?.top_rejected_drugs && metrics.top_rejected_drugs.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-sm font-semibold text-slate-900 mb-4">Top Rejected Drugs</h3>
            <div className="space-y-2">
              {metrics.top_rejected_drugs.map((drug, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                  <span className="text-sm text-slate-700">{drug.drug}</span>
                  <span className="text-sm font-medium text-red-600">{drug.count} denials</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Agent Performance */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200">
            <h3 className="text-sm font-semibold text-slate-900">Agent Performance</h3>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Agent</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Executions</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Success Rate</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Avg Duration</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Tokens Used</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {agentMetrics.length === 0 ? (
                <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">No agent data yet.</td></tr>
              ) : (
                agentMetrics.map((a) => (
                  <tr key={a.agent_name} className="hover:bg-slate-50">
                    <td className="px-5 py-3 font-medium">{a.agent_name.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</td>
                    <td className="px-5 py-3">{a.total_executions}</td>
                    <td className="px-5 py-3">
                      <span className={a.success_rate >= 90 ? "text-emerald-600" : a.success_rate >= 70 ? "text-amber-600" : "text-red-600"}>
                        {a.success_rate.toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-5 py-3">{a.average_duration_ms.toFixed(0)}ms</td>
                    <td className="px-5 py-3">{a.total_tokens_used.toLocaleString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
