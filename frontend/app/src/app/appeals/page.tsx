"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { api } from "@/lib/api";
import type { Appeal } from "@/lib/types";

export default function AppealsPage() {
  const [appeals, setAppeals] = useState<Appeal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.appeals.list();
        setAppeals(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <>
      <Header title="Appeals" />
      <div className="p-6">
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Appeal #</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Level</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Denial Reason</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Decision</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={6} className="px-5 py-8 text-center text-slate-400">Loading...</td></tr>
              ) : appeals.length === 0 ? (
                <tr><td colSpan={6} className="px-5 py-8 text-center text-slate-400">No appeals yet.</td></tr>
              ) : (
                appeals.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50">
                    <td className="px-5 py-3 font-mono text-xs">{a.appeal_number || a.id.slice(0, 8)}</td>
                    <td className="px-5 py-3">Level {a.level}</td>
                    <td className="px-5 py-3 capitalize">{a.status}</td>
                    <td className="px-5 py-3 text-slate-600 max-w-xs truncate">{a.denial_reason || "—"}</td>
                    <td className="px-5 py-3 font-medium">{a.decision || "Pending"}</td>
                    <td className="px-5 py-3 text-slate-500">{new Date(a.created_at).toLocaleDateString()}</td>
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
