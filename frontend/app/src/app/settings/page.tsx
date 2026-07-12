"use client";

import Header from "@/components/layout/Header";

export default function SettingsPage() {
  return (
    <>
      <Header title="Settings" />
      <div className="p-6 max-w-2xl space-y-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="font-semibold text-slate-900 mb-4">API Configuration</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-600 mb-1">Backend API URL</label>
              <input
                type="text"
                defaultValue={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                disabled
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm bg-slate-50"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-600 mb-1">Environment</label>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                Development
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Pharmacy Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-600 mb-1">Pharmacy Name</label>
              <input className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="Your Pharmacy" />
            </div>
            <div>
              <label className="block text-sm text-slate-600 mb-1">NPI</label>
              <input className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="10-digit NPI" />
            </div>
            <div>
              <label className="block text-sm text-slate-600 mb-1">Phone</label>
              <input className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="(555) 123-4567" />
            </div>
            <div>
              <label className="block text-sm text-slate-600 mb-1">Fax</label>
              <input className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="(555) 123-4568" />
            </div>
          </div>
          <button className="mt-4 px-4 py-2 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700">
            Save Settings
          </button>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Notification Preferences</h3>
          <div className="space-y-3">
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="rounded border-slate-300" />
              <span className="text-sm text-slate-700">Email notifications for PA approvals</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="rounded border-slate-300" />
              <span className="text-sm text-slate-700">SMS alerts for PA denials</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="rounded border-slate-300" />
              <span className="text-sm text-slate-700">Daily analytics summary email</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" className="rounded border-slate-300" />
              <span className="text-sm text-slate-700">Escalation alerts (when PA needs human review)</span>
            </label>
          </div>
        </div>
      </div>
    </>
  );
}
