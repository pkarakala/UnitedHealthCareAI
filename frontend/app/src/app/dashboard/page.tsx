"use client";

import { useEffect, useState, useCallback } from "react";
import Header from "@/components/layout/Header";
import { StatCard, StatusBadge, SkeletonRows, ErrorBanner, PriorityBadge, UpdatedAgo } from "@/components/ui";
import { usePolling } from "@/hooks/usePolling";
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
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [m, pas] = await Promise.all([
        api.analytics.dashboard(),
        api.priorAuths.list({ limit: 10 }),
      ]);
      setMetrics(m);
      setRecentPAs(pas);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const { lastUpdated, refresh } = usePolling(load, { interval: 30_000 });

  const needsAttention = recentPAs.filter(
    (pa) => pa.escalated || pa.status === "error" || pa.status === "awaiting_records" || pa.status === "doctor_outreach"
  );

  return (
    <>
      <Header title="Dashboard" />
      <div className="p-6 space-y-6 max-w-[1400px]">
        {error && <ErrorBanner message={error} onRetry={load} />}

        {/* Needs Attention */}
        {needsAttention.length > 0 && (
          <div className="bg-amber-50/50 border border-amber-200/60 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              <h3 className="text-[13px] font-semibold text-amber-900">
                Needs Attention ({needsAttention.length})
              </h3>
            </div>
            <div className="space-y-1.5">
              {needsAttention.slice(0, 5).map((pa) => (
                <Link
                  key={pa.id}
                  href={`/prior-auths/${pa.id}`}
                  className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-amber-100/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-[12px] text-amber-800">{pa.pa_number || pa.id.slice(0, 8)}</span>
                    <StatusBadge status={pa.status} />
                    {pa.escalated && (
                      <span className="text-[10px] uppercase tracking-wide bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-medium">
                        Escalated
                      </span>
                    )}
                  </div>
                  <span className={`text-[11px] font-medium ${getAgeColor(pa.created_at)}`}>
                    {formatAge(pa.created_at)}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}

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
            icon={<TrendingUp className="w-5 h-5 text-teal-500" />}
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
            icon={<CheckCircle2 className="w-5 h-5 text-teal-400" />}
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
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-[14px] font-semibold text-slate-900">Recent Prior Authorizations</h3>
              <p className="text-[12px] text-slate-500 mt-0.5">Latest PA cases across all statuses</p>
            </div>
            <div className="flex items-center gap-4">
              <UpdatedAgo lastUpdated={lastUpdated} onRefresh={refresh} />
              <Link
                href="/prior-auths"
                className="text-[12px] font-medium text-teal-600 hover:text-teal-700 flex items-center gap-1 transition-colors"
              >
                View all <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-slate-50/50">
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Case</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Status</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Agent</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Priority</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Age</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {loading ? (
                  <SkeletonRows columns={5} rows={6} />
                ) : recentPAs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-16 text-center">
                      <div className="flex flex-col items-center">
                        <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-3">
                          <FileText className="w-6 h-6 text-slate-300" />
                        </div>
                        <p className="text-sm font-medium text-slate-500">No prior authorizations yet</p>
                        <p className="text-[12px] text-slate-500 mt-1">Start by intaking a new prescription</p>
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
                      <td className="px-5 py-3">
                        <Link href={`/prior-auths/${pa.id}`} className="font-mono text-[12px] text-teal-600 hover:underline">
                          {pa.pa_number || pa.id.slice(0, 8)}
                        </Link>
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge status={pa.status} />
                      </td>
                      <td className="px-5 py-3 text-slate-600">
                        {pa.current_agent?.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()) || "—"}
                      </td>
                      <td className="px-5 py-3">
                        <PriorityBadge priority={pa.priority} />
                      </td>
                      <td className={`px-5 py-3 text-[12px] font-medium ${getAgeColor(pa.created_at)}`}>
                        {formatAge(pa.created_at)}
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

function formatAge(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 3_600_000);
  if (hours < 1) return "< 1h";
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  return `${days}d`;
}

function getAgeColor(dateStr: string): string {
  const hours = (Date.now() - new Date(dateStr).getTime()) / 3_600_000;
  if (hours > 72) return "text-red-600";
  if (hours > 24) return "text-amber-600";
  return "text-slate-400";
}
