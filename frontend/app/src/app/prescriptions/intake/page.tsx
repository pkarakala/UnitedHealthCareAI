"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import { api } from "@/lib/api";

export default function IntakePage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ prior_auth_id: string; message: string } | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError("");

    const form = new FormData(e.currentTarget);

    try {
      const res = await api.prescriptions.intake({
        patient_id: form.get("patient_id") as string,
        prescriber_npi: form.get("prescriber_npi") as string,
        drug_name: form.get("drug_name") as string,
        prescriber_name: form.get("prescriber_name") as string || undefined,
        prescriber_phone: form.get("prescriber_phone") as string || undefined,
        prescriber_fax: form.get("prescriber_fax") as string || undefined,
        strength: form.get("strength") as string || undefined,
        quantity: form.get("quantity") ? Number(form.get("quantity")) : undefined,
        days_supply: form.get("days_supply") ? Number(form.get("days_supply")) : undefined,
        directions: form.get("directions") as string || undefined,
        ndc: form.get("ndc") as string || undefined,
      });
      setResult(res);
    } catch (e: any) {
      setError(e.message || "Failed to submit prescription");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Header title="New Prescription Intake" />
      <div className="p-6 max-w-3xl">
        {result ? (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-emerald-800">Intake Successful</h3>
            <p className="text-sm text-emerald-700 mt-2">{result.message}</p>
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => router.push(`/prior-auths/${result.prior_auth_id}`)}
                className="px-4 py-2 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700"
              >
                View PA Case
              </button>
              <button
                onClick={() => { setResult(null); setError(""); }}
                className="px-4 py-2 bg-white border border-slate-200 text-sm rounded-lg hover:bg-slate-50"
              >
                Intake Another
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 p-6 space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg">{error}</div>
            )}

            {/* Patient & Prescriber */}
            <fieldset className="space-y-4">
              <legend className="text-sm font-semibold text-slate-900">Patient & Prescriber</legend>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Patient ID *</label>
                  <input name="patient_id" required className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="UUID from patient record" />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Prescriber NPI *</label>
                  <input name="prescriber_npi" required maxLength={10} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="10-digit NPI" />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Prescriber Name</label>
                  <input name="prescriber_name" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="Dr. Smith" />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Prescriber Phone</label>
                  <input name="prescriber_phone" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="5551234567" />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Prescriber Fax</label>
                  <input name="prescriber_fax" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="5551234568" />
                </div>
              </div>
            </fieldset>

            {/* Medication */}
            <fieldset className="space-y-4">
              <legend className="text-sm font-semibold text-slate-900">Medication</legend>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Drug Name *</label>
                  <input name="drug_name" required className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="Ozempic" />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Strength</label>
                  <input name="strength" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="1mg/dose" />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">NDC</label>
                  <input name="ndc" maxLength={11} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="00169416112" />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Quantity</label>
                  <input name="quantity" type="number" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="4" />
                </div>
                <div>
                  <label className="block text-sm text-slate-600 mb-1">Days Supply</label>
                  <input name="days_supply" type="number" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="28" />
                </div>
              </div>
              <div>
                <label className="block text-sm text-slate-600 mb-1">Directions (Sig)</label>
                <textarea name="directions" rows={2} className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" placeholder="Inject 1mg subcutaneously once weekly" />
              </div>
            </fieldset>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? "Processing..." : "Submit Prescription & Start PA Workflow"}
            </button>
          </form>
        )}
      </div>
    </>
  );
}
