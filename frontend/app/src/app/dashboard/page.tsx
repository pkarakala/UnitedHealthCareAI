"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import StatCard from "@/components/ui/StatCard";
import StatusBadge from "@/components/ui/StatusBadge";
import { api } from "@/lib/api";
import type { DashboardMetrics, PriorAuth } from "@/lib/types";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentPAs, setRecentPAs] = useState<PriorAuth[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [m, pas] = await Promise.all([
          api.analytics.dashboard(),
          api.priorAuths.list({ limit: 10 }),
        ]);
        setMetrics(m);
        setRecentPAs(pas);
      } catch (e) {
        console.error("Failed to load dashboard:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <>
        <Header title="Dashboard" />
        <div className="p-6 flex items-center justify-center h-64">
          <p className="text-slate-500">Loading dashboard...</p>
        </div>
      </>
    );
  }

  return (
    <>
      <Header title="Dashboard" />
      <div className="p-6 space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total PAs"
            value={metrics?.total_pas ?? 0}
            subtitle="All time"
            color="blue"
          />
          <StatCard
            title="Pending"
            value={metrics?.pending_pas ?? 0}
            subtitle="Awaiting decision"
            color="amber"
          />
          <StatCard
            title="Approval Rate"
            value={`${(metrics?.approval_rate ?? 0).toFixed(1)}%`}
            subtitle="Overall"
            color="emerald"
          />
          <StatCard
            title="Revenue Recovered"
            value={`$${(metrics?.revenue_recovered_mtd ?? 0).toLocaleString()}`}
            subtitle="Month to date"
            color="emerald"
          />
        </div>

        {/* Secondary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            title="Avg Turnaround"
            value={`${(metrics?.average_turnaround_hours ?? 0).toFixed(0)}h`}
            subtitle="Intake to decision"
            color="blue"
          />
          <StatCard
            title="Appeal Success"
            value={`${(metrics?.appeal_success_rate ?? 0).toFixed(0)}%`}
            subtitle="Appeals won"
            color="amber"
          />
          <StatCard
            title="Approved Today"
            value={metrics?.approved_today ?? 0}
            subtitle={`${metrics?.denied_today ?? 0} denied`}
            color="emerald"
          />
        </div>

        {/* Recent PAs Table */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200">
            <h3 className="text-sm font-semibold text-slate-900">Recent Prior Authorizations</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">PA ID</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">Status</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">Agent</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">Priority</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-600">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentPAs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-8 text-center text-slate-400">
                      No prior authorizations yet. Start by intaking a prescription.
                    </td>
                  </tr>
                ) : (
                  recentPAs.map((pa) => (
                    <tr key={pa.id} className="hover:bg-slate-50 cursor-pointer">
                      <td className="px-5 py-3 font-mono text-xs">{pa.id.slice(0, 8)}...</td>
                      <td className="px-5 py-3">
                        <StatusBadge status={pa.status} />
                      </td>
                      <td className="px-5 py-3 text-slate-600">{pa.current_agent || "—"}</td>
                      <td className="px-5 py-3">{pa.priority}</td>
                      <td className="px-5 py-3 text-slate-500">
                        {new Date(pa.created_at).toLocaleDateString()}
                      </td>
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
