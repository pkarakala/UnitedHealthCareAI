"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { api } from "@/lib/api";
import type { Patient } from "@/lib/types";
import { Users, Plus, Search, X } from "lucide-react";

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    loadPatients();
  }, [search]);

  async function loadPatients() {
    try {
      const data = await api.patients.list({ search: search || undefined });
      setPatients(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      await api.patients.create({
        first_name: form.get("first_name") as string,
        last_name: form.get("last_name") as string,
        date_of_birth: form.get("date_of_birth") as string,
        phone: (form.get("phone") as string) || undefined,
        email: (form.get("email") as string) || undefined,
        member_id: (form.get("member_id") as string) || undefined,
      });
      setShowForm(false);
      loadPatients();
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <>
      <Header title="Patients" />
      <div className="p-8 space-y-6 max-w-[1400px]">
        {/* Controls */}
        <div className="flex items-center justify-between">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name or member ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm w-72 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
            />
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className={`inline-flex items-center gap-2 px-4 py-2.5 text-[13px] font-medium rounded-lg transition-all ${
              showForm
                ? "bg-slate-100 text-slate-600 hover:bg-slate-200"
                : "bg-teal-600 text-white hover:bg-teal-700 shadow-sm shadow-teal-600/20"
            }`}
          >
            {showForm ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
            {showForm ? "Cancel" : "New Patient"}
          </button>
        </div>

        {/* Create Form */}
        {showForm && (
          <form onSubmit={handleCreate} className="bg-white rounded-xl border border-slate-200/80 p-6">
            <h3 className="text-[14px] font-semibold text-slate-900 mb-4">Add New Patient</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <input name="first_name" required placeholder="First Name *" className="border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
              <input name="last_name" required placeholder="Last Name *" className="border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
              <input name="date_of_birth" type="date" required className="border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
              <input name="phone" placeholder="Phone" className="border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
              <input name="email" type="email" placeholder="Email" className="border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
              <input name="member_id" placeholder="Member ID" className="border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500" />
            </div>
            <button type="submit" className="mt-4 inline-flex items-center gap-2 px-5 py-2.5 bg-teal-600 text-white text-[13px] font-medium rounded-lg hover:bg-teal-700 transition-colors">
              <Plus className="w-3.5 h-3.5" /> Create Patient
            </button>
          </form>
        )}

        {/* Table */}
        <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="bg-slate-50/50">
                <th className="px-6 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Date of Birth</th>
                <th className="px-6 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Member ID</th>
                <th className="px-6 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Phone</th>
                <th className="px-6 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Email</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <div className="flex items-center justify-center gap-2 text-slate-400">
                      <div className="w-4 h-4 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
                      <span className="text-sm">Loading patients...</span>
                    </div>
                  </td>
                </tr>
              ) : patients.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-16 text-center">
                    <div className="flex flex-col items-center">
                      <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-3">
                        <Users className="w-6 h-6 text-slate-300" />
                      </div>
                      <p className="text-sm font-medium text-slate-500">No patients found</p>
                      <p className="text-[12px] text-slate-400 mt-1">Add a patient to get started</p>
                    </div>
                  </td>
                </tr>
              ) : (
                patients.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-3.5 font-medium text-slate-900">{p.first_name} {p.last_name}</td>
                    <td className="px-6 py-3.5 text-slate-600">{p.date_of_birth}</td>
                    <td className="px-6 py-3.5 font-mono text-[12px] text-slate-500">{p.member_id || "—"}</td>
                    <td className="px-6 py-3.5 text-slate-600">{p.phone || "—"}</td>
                    <td className="px-6 py-3.5 text-slate-600">{p.email || "—"}</td>
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
