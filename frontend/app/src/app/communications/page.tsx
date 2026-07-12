"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { api } from "@/lib/api";
import type { Communication } from "@/lib/types";

export default function CommunicationsPage() {
  const [comms, setComms] = useState<Communication[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.communications.list();
        setComms(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const channelIcon: Record<string, string> = {
    fax: "📠",
    email: "📧",
    sms: "💬",
    phone: "📞",
    portal: "🖥️",
  };

  return (
    <>
      <Header title="Communications" />
      <div className="p-6">
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Channel</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Recipient</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Subject</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Sent</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={6} className="px-5 py-8 text-center text-slate-400">Loading...</td></tr>
              ) : comms.length === 0 ? (
                <tr><td colSpan={6} className="px-5 py-8 text-center text-slate-400">No communications yet.</td></tr>
              ) : (
                comms.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="px-5 py-3">
                      <span className="mr-1">{channelIcon[c.channel] || "📨"}</span>
                      {c.channel.toUpperCase()}
                    </td>
                    <td className="px-5 py-3">{c.recipient}</td>
                    <td className="px-5 py-3 text-slate-600 max-w-xs truncate">{c.subject || "—"}</td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        c.status === "sent" || c.status === "delivered" ? "bg-emerald-100 text-emerald-700" :
                        c.status === "failed" ? "bg-red-100 text-red-700" :
                        "bg-amber-100 text-amber-700"
                      }`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-500">
                      {c.sent_at ? new Date(c.sent_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-5 py-3">
                      {c.status === "failed" && (
                        <button
                          onClick={async () => {
                            await api.communications.resend(c.id);
                            window.location.reload();
                          }}
                          className="text-xs text-emerald-600 hover:underline"
                        >
                          Resend
                        </button>
                      )}
                    </td>
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
