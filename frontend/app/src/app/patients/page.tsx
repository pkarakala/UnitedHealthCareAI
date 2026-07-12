"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import { api } from "@/lib/api";
import type { Patient } from "@/lib/types";

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
        phone: form.get("phone") as string || undefined,
        email: form.get("email") as string || undefined,
        member_id: form.get("member_id") as string || undefined,
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
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <input
            type="text"
            placeholder="Search patients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border border-slate-300 rounded-lg px-4 py-2 text-sm w-64"
          />
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700"
          >
            {showForm ? "Cancel" : "+ New Patient"}
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="bg-white rounded-xl border border-slate-200 p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <input name="first_name" required placeholder="First Name *" className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
              <input name="last_name" required placeholder="Last Name *" className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
              <input name="date_of_birth" type="date" required className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
              <input name="phone" placeholder="Phone" className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
              <input name="email" type="email" placeholder="Email" className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
              <input name="member_id" placeholder="Member ID" className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
            </div>
            <button type="submit" className="mt-4 px-4 py-2 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700">
              Create Patient
            </button>
          </form>
        )}

        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Name</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">DOB</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Member ID</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Phone</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Email</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">Loading...</td></tr>
              ) : patients.length === 0 ? (
                <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">No patients found.</td></tr>
              ) : (
                patients.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50">
                    <td className="px-5 py-3 font-medium">{p.first_name} {p.last_name}</td>
                    <td className="px-5 py-3 text-slate-600">{p.date_of_birth}</td>
                    <td className="px-5 py-3 font-mono text-xs">{p.member_id || "—"}</td>
                    <td className="px-5 py-3 text-slate-600">{p.phone || "—"}</td>
                    <td className="px-5 py-3 text-slate-600">{p.email || "—"}</td>
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
