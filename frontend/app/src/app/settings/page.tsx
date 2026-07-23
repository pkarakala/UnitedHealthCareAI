"use client";

import Header from "@/components/layout/Header";
import { Button, Input } from "@/components/ui";

export default function SettingsPage() {
  return (
    <>
      <Header title="Settings" />
      <div className="p-6 max-w-2xl space-y-6">
        <div className="bg-white rounded-xl border border-slate-200/80 p-5">
          <h3 className="text-[13px] font-semibold text-slate-900 mb-4">API Configuration</h3>
          <div className="space-y-4">
            <Input
              label="Backend API URL"
              defaultValue={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
              disabled
            />
            <div>
              <p className="text-[12px] font-medium text-slate-500 mb-1.5">Environment</p>
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium ring-1 ring-inset bg-amber-50 text-amber-700 ring-amber-200">
                Development
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/80 p-5">
          <h3 className="text-[13px] font-semibold text-slate-900 mb-4">Pharmacy Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input label="Pharmacy Name" name="pharmacy_name" placeholder="Your Pharmacy" />
            <Input label="NPI" name="npi" placeholder="10-digit NPI" />
            <Input label="Phone" name="phone" placeholder="(555) 123-4567" />
            <Input label="Fax" name="fax" placeholder="(555) 123-4568" />
          </div>
          <div className="mt-4">
            <Button>Save Settings</Button>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/80 p-5">
          <h3 className="text-[13px] font-semibold text-slate-900 mb-4">Notification Preferences</h3>
          <div className="space-y-3">
            {[
              { label: "Email notifications for PA approvals", defaultChecked: true },
              { label: "SMS alerts for PA denials", defaultChecked: true },
              { label: "Daily analytics summary email", defaultChecked: true },
              { label: "Escalation alerts (when PA needs human review)", defaultChecked: false },
            ].map((item) => (
              <label key={item.label} className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  defaultChecked={item.defaultChecked}
                  className="rounded border-slate-300 text-teal-600 focus:ring-teal-500/20"
                />
                <span className="text-[13px] text-slate-700">{item.label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
