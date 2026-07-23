"use client";

import { useEffect, useState, useCallback } from "react";
import Header from "@/components/layout/Header";
import { Button, Input, SkeletonRows, ErrorBanner } from "@/components/ui";
import { useDebounce } from "@/hooks/useDebounce";
import { api } from "@/lib/api";
import type { Patient } from "@/lib/types";
import { Users, Plus, Search, X } from "lucide-react";

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const debouncedSearch = useDebounce(search, 300);

  const loadPatients = useCallback(async () => {
    setError(null);
    try {
      const data = await api.patients.list({ search: debouncedSearch || undefined });
      setPatients(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load patients");
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch]);

  useEffect(() => { loadPatients(); }, [loadPatients]);

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
      setError(e instanceof Error ? e.message : "Failed to create patient");
    }
  }

  return (
    <>
      <Header title="Patients" />
      <div className="p-6 space-y-5 max-w-[1400px]">
        {error && <ErrorBanner message={error} onRetry={loadPatients} />}

        {/* Controls */}
        <div className="flex items-center justify-between gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name or member ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search patients"
              className="pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-[13px] w-72 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
            />
          </div>
          <Button
            variant={showForm ? "secondary" : "primary"}
            icon={showForm ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
            onClick={() => setShowForm(!showForm)}
          >
            {showForm ? "Cancel" : "New Patient"}
          </Button>
        </div>

        {/* Create Form */}
        {showForm && (
          <form onSubmit={handleCreate} className="bg-white rounded-xl border border-slate-200/80 p-5">
            <h3 className="text-[13px] font-semibold text-slate-900 mb-4">Add New Patient</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input name="first_name" label="First Name *" required placeholder="Jane" />
              <Input name="last_name" label="Last Name *" required placeholder="Smith" />
              <Input name="date_of_birth" label="Date of Birth *" type="date" required />
              <Input name="phone" label="Phone" placeholder="(555) 123-4567" />
              <Input name="email" label="Email" type="email" placeholder="jane@example.com" />
              <Input name="member_id" label="Member ID" placeholder="MBR12345" />
            </div>
            <div className="mt-4">
              <Button type="submit" icon={<Plus className="w-3.5 h-3.5" />}>
                Create Patient
              </Button>
            </div>
          </form>
        )}

        {/* Table */}
        <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-slate-50/50">
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Name</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Date of Birth</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Member ID</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Phone</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500 text-[11px] uppercase tracking-wider">Email</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {loading ? (
                  <SkeletonRows columns={5} rows={6} />
                ) : patients.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-5 py-16 text-center">
                      <div className="flex flex-col items-center">
                        <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-3">
                          <Users className="w-6 h-6 text-slate-300" />
                        </div>
                        <p className="text-sm font-medium text-slate-500">No patients found</p>
                        <p className="text-[12px] text-slate-400 mt-1">
                          {debouncedSearch ? "Try a different search" : "Add a patient to get started"}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  patients.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-5 py-3 font-medium text-slate-900">
                        {p.last_name}, {p.first_name}
                      </td>
                      <td className="px-5 py-3 text-slate-600">{p.date_of_birth}</td>
                      <td className="px-5 py-3 font-mono text-[12px] text-slate-500">{p.member_id || "—"}</td>
                      <td className="px-5 py-3 text-slate-600">{p.phone || "—"}</td>
                      <td className="px-5 py-3 text-slate-600">{p.email || "—"}</td>
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
