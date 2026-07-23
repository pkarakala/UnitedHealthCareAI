"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/layout/Header";
import { api } from "@/lib/api";
import { CheckCircle2, ArrowRight, Pill, User, Stethoscope } from "lucide-react";

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
        prescriber_name: (form.get("prescriber_name") as string) || undefined,
        prescriber_phone: (form.get("prescriber_phone") as string) || undefined,
        prescriber_fax: (form.get("prescriber_fax") as string) || undefined,
        strength: (form.get("strength") as string) || undefined,
        quantity: form.get("quantity") ? Number(form.get("quantity")) : undefined,
        days_supply: form.get("days_supply") ? Number(form.get("days_supply")) : undefined,
        directions: (form.get("directions") as string) || undefined,
        ndc: (form.get("ndc") as string) || undefined,
      });
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to submit prescription");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Header title="New Prescription Intake" />
      <div className="p-8 max-w-3xl">
        {result ? (
          <div className="bg-white rounded-2xl border border-emerald-200 p-10 text-center">
            <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-7 h-7 text-emerald-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900">Intake Successful</h3>
            <p className="text-sm text-slate-500 mt-2 max-w-md mx-auto">{result.message}</p>
            <div className="mt-6 flex items-center justify-center gap-3">
              <button
                onClick={() => router.push(`/prior-auths/${result.prior_auth_id}`)}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-teal-600 text-white text-[13px] font-medium rounded-lg hover:bg-teal-700 transition-colors"
              >
                View PA Case <ArrowRight className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => { setResult(null); setError(""); }}
                className="px-5 py-2.5 bg-white border border-slate-200 text-[13px] font-medium text-slate-600 rounded-lg hover:bg-slate-50 transition-colors"
              >
                Intake Another
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-xl">{error}</div>
            )}

            {/* Patient & Prescriber */}
            <div className="bg-white rounded-xl border border-slate-200/80 p-6">
              <div className="flex items-center gap-2 mb-5">
                <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
                  <User className="w-4 h-4 text-blue-500" />
                </div>
                <h3 className="text-[14px] font-semibold text-slate-900">Patient & Prescriber</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[12px] font-medium text-slate-500 mb-1.5">Patient ID *</label>
                  <input name="patient_id" required className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all" placeholder="Patient UUID" />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-slate-500 mb-1.5">Prescriber NPI *</label>
                  <input name="prescriber_npi" required maxLength={10} className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all" placeholder="10-digit NPI" />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-slate-500 mb-1.5">Prescriber Name</label>
                  <input name="prescriber_name" className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all" placeholder="Dr. Smith" />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-slate-500 mb-1.5">Prescriber Phone</label>
                  <input name="prescriber_phone" className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all" placeholder="(555) 123-4567" />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-slate-500 mb-1.5">Prescriber Fax</label>
                  <input name="prescriber_fax" className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all" placeholder="(555) 123-4568" />
                </div>
              </div>
            </div>

            {/* Medication */}
            <div className="bg-white rounded-xl border border-slate-200/80 p-6">
              <div className="flex items-center gap-2 mb-5">
                <div className="w-8 h-8 bg-purple-50 rounded-lg flex items-center justify-center">
                  <Pill className="w-4 h-4 text-purple-500" />
                </div>
                <h3 className="text-[14px] font-semibold text-slate-900">Medication Details</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[12px] font-medium text-slate-500 mb-1.5">Drug Name *</label>
                  <input name="drug_name" required className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all" placeholder="Ozempic" />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-slate-500 mb-1.5">Strength</label>
                  <input name="strength" className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all" placeholder="1mg/dose" />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-slate-500 mb-1.5">NDC</label>
                  <input name="ndc" maxLength={11} className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all" placeholder="00169416112" />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-slate-500 mb-1.5">Quantity</label>
                  <input name="quantity" type="number" className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all" placeholder="4" />
                </div>
                <div>
                  <label className="block text-[12px] font-medium text-slate-500 mb-1.5">Days Supply</label>
                  <input name="days_supply" type="number" className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all" placeholder="28" />
                </div>
              </div>
              <div className="mt-4">
                <label className="block text-[12px] font-medium text-slate-500 mb-1.5">Directions (Sig)</label>
                <textarea name="directions" rows={2} className="w-full border border-slate-200 rounded-lg px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all resize-none" placeholder="Inject 1mg subcutaneously once weekly" />
              </div>
            </div>

            {/* Submit */}
            <div className="bg-white rounded-xl border border-slate-200/80 p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-teal-50 rounded-lg flex items-center justify-center">
                  <Stethoscope className="w-4 h-4 text-teal-500" />
                </div>
                <div>
                  <h3 className="text-[14px] font-semibold text-slate-900">Submit & Start Workflow</h3>
                  <p className="text-[12px] text-slate-500">AI agents will process this prescription automatically</p>
                </div>
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 bg-gradient-to-r from-teal-600 to-teal-700 text-white text-[13px] font-medium rounded-lg hover:from-teal-700 hover:to-teal-800 disabled:from-slate-300 disabled:to-slate-300 disabled:cursor-not-allowed transition-all shadow-sm shadow-teal-600/20 flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    Submit Prescription
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </>
  );
}
