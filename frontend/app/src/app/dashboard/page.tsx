"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import StatCard from "@/components/ui/StatCard";
import StatusBadge from "@/components/ui/StatusBadge";
import { api } from "@/lib/api";
import type { DashboardMetrics, PriorAuth } from "@/lib/types";
import {
  FileText,
  Clock,
  TrendingUp,
  DollarSign,
  Zap,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  PlusCircle,
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [recentPAs, setRecentPAs] = useState<PriorAuth[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [m, pas] = await Promise.all([
          api.analytics.dashboard(),
          api.priorAuths.list({ limit: 8 }),
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
        <div className="p-8 flex items-center justify-center h-64">
          <div className="flex items-center gap-3 text-slate-400">
            <div className="w-5 h-5 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm">Loading dashboard...</span>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header title="Dashboard" />
      <div className="p-8 space-y-8 max-w-[1400px]">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-2xl p-8 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-teal-500/10 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-1/2 w-32 h-32 bg-teal-500/5 rounded-full translate-y-1/2" />
          <div className="relative">
            <p className="text-teal-400 text-[12px] font-medium uppercase tracking-wider">Overview</p>
            <h2 className="text-xl font-semibold mt-1">Prior Authorization Command Center</h2>
            <p className="text-slate-400 text-sm mt-2 max-w-lg">
              Monitor your PA workflow performance, track approvals in real-time, and let AI agents handle the heavy lifting.
            </p>
          </div>
        </div>

        {/* Primary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total PAs"
            value={metrics?.total_pas ?? 0}
            subtitle="All time"
            icon={<FileText className="w-5 h-5 text-slate-400" />}
          />
          <StatCard
            title="Pending"
            value={metrics?.pending_pas ?? 0}
            subtitle="Awaiting decision"
            icon={<Clock className="w-5 h-5 text-amber-400" />}
          />
          <StatCard
            title="Approval Rate"
            value={`${(metrics?.approval_rate ?? 0).toFixed(1)}%`}
            subtitle="Overall performance"
            trend="up"
            icon={<TrendingUp className="w-5 h-5 text-emerald-500" />}
          />
          <StatCard
            title="Revenue Recovered"
            value={`$${(metrics?.revenue_recovered_mtd ?? 0).toLocaleString()}`}
            subtitle="Month to date"
            trend="up"
            icon={<DollarSign className="w-5 h-5 text-teal-500" />}
          />
        </div>

        {/* Secondary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            title="Avg Turnaround"
            value={`${(metrics?.average_turnaround_hours ?? 0).toFixed(0)}h`}
            subtitle="Intake to decision"
            icon={<Zap className="w-5 h-5 text-indigo-400" />}
          />
          <StatCard
            title="Appeal Success"
            value={`${(metrics?.appeal_success_rate ?? 0).toFixed(0)}%`}
            subtitle="Appeals won"
            icon={<CheckCircle2 className="w-5 h-5 text-emerald-400" />}
          />
          <StatCard
            title="Approved Today"
            value={metrics?.approved_today ?? 0}
            subtitle={`${metrics?.denied_today ?? 0} denied`}
            icon={<AlertCircle className="w-5 h-5 text-amber-400" />}
          />
        </div>

        {/* Recent PAs Table */}
        <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-[14px] font-semibold text-slate-900">Recent Prior Authorizations</h3>
              <p className="text-[12px] text-slate-400 mt-0.5">Latest PA cases across all statuses</p>
            </div>
            <Link
              href="/prior-auths"
              className="text-[12px] font-medium text-teal-600 hover:text-teal-700 flex items-center gap-1 transition-colors"
            >
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-slate-50/50">
                  <th className="px-6 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">PA ID</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Agent</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Priority</th>
                  <th className="px-6 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {recentPAs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-16 text-center">
                      <div className="flex flex-col items-center">
                        <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-3">
                          <FileText className="w-6 h-6 text-slate-300" />
                        </div>
                        <p className="text-sm font-medium text-slate-500">No prior authorizations yet</p>
                        <p className="text-[12px] text-slate-400 mt-1">Start by intaking a new prescription</p>
                        <Link
                          href="/prescriptions/intake"
                          className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white text-[12px] font-medium rounded-lg hover:bg-teal-700 transition-colors"
                        >
                          <PlusCircle className="w-3.5 h-3.5" />
                          New Intake
                        </Link>
                      </div>
                    </td>
                  </tr>
                ) : (
                  recentPAs.map((pa) => (
                    <tr key={pa.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-6 py-3.5">
                        <Link href={`/prior-auths/${pa.id}`} className="font-mono text-[12px] text-teal-600 hover:underline">
                          {pa.id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="px-6 py-3.5">
                        <StatusBadge status={pa.status} />
                      </td>
                      <td className="px-6 py-3.5 text-slate-600">
                        {pa.current_agent?.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()) || "—"}
                      </td>
                      <td className="px-6 py-3.5">
                        <span className={`inline-flex items-center justify-center w-6 h-6 rounded-md text-[11px] font-semibold ${
                          pa.priority <= 3 ? "bg-red-50 text-red-600" :
                          pa.priority <= 5 ? "bg-amber-50 text-amber-600" :
                          "bg-slate-50 text-slate-500"
                        }`}>
                          {pa.priority}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 text-slate-400 text-[12px]">
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
