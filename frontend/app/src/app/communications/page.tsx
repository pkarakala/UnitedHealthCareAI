"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { Spinner, ErrorBanner, Button } from "@/components/ui";
import { api } from "@/lib/api";
import type { Communication } from "@/lib/types";
import { Printer, Mail, MessageCircle, Phone, Monitor, MessageSquare } from "lucide-react";

const channelIcons: Record<string, React.ReactNode> = {
  fax: <Printer className="w-3.5 h-3.5" />,
  email: <Mail className="w-3.5 h-3.5" />,
  sms: <MessageCircle className="w-3.5 h-3.5" />,
  phone: <Phone className="w-3.5 h-3.5" />,
  portal: <Monitor className="w-3.5 h-3.5" />,
};

export default function CommunicationsPage() {
  const [comms, setComms] = useState<Communication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setLoading(true);
    try {
      const data = await api.communications.list();
      setComms(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load communications");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <>
      <Header title="Communications" />
      <div className="p-6">
        {error && <ErrorBanner message={error} onRetry={load} />}

        <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden mt-4">
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-slate-50/50">
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Channel</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Recipient</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Subject</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Status</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Sent</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {loading ? (
                  <tr><td colSpan={6}><Spinner label="Loading..." /></td></tr>
                ) : comms.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-16 text-center">
                      <div className="flex flex-col items-center">
                        <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-3">
                          <MessageSquare className="w-6 h-6 text-slate-300" />
                        </div>
                        <p className="text-sm font-medium text-slate-500">No communications yet</p>
                        <p className="text-[12px] text-slate-500 mt-1">Communications are created during PA processing</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  comms.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2 text-slate-600">
                          <span className="text-slate-400">{channelIcons[c.channel] || <Mail className="w-3.5 h-3.5" />}</span>
                          <span className="capitalize">{c.channel}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-slate-700">{c.recipient}</td>
                      <td className="px-5 py-3 text-slate-600 max-w-xs truncate">{c.subject || "—"}</td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium ring-1 ring-inset ${
                          c.status === "sent" || c.status === "delivered"
                            ? "bg-teal-50 text-teal-700 ring-teal-200"
                            : c.status === "failed"
                            ? "bg-red-50 text-red-600 ring-red-200"
                            : "bg-amber-50 text-amber-700 ring-amber-200"
                        }`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-slate-500 text-[12px]">
                        {c.sent_at ? new Date(c.sent_at).toLocaleString() : "—"}
                      </td>
                      <td className="px-5 py-3">
                        {c.status === "failed" && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={async () => {
                              await api.communications.resend(c.id);
                              load();
                            }}
                          >
                            Resend
                          </Button>
                        )}
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
