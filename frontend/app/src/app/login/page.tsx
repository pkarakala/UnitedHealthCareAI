"use client";

import { useRouter } from "next/navigation";
import { Activity, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();

  function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    router.push("/dashboard");
  }

  return (
    <div className="w-full max-w-[420px] mx-auto p-6">
      {/* Logo */}
      <div className="text-center mb-10">
        <div className="w-12 h-12 bg-gradient-to-br from-teal-500 to-teal-700 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-teal-500/20">
          <Activity className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          USA<span className="text-teal-600">Healthcare</span>.AI
        </h1>
        <p className="text-sm text-slate-500 mt-1.5">Prior Authorization Platform</p>
      </div>

      {/* Login Card */}
      <form onSubmit={handleLogin} className="bg-white rounded-2xl border border-slate-200/80 p-8 shadow-sm">
        <h2 className="text-[15px] font-semibold text-slate-900 mb-6">Sign in to your account</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-[12px] font-medium text-slate-600 mb-1.5">Email address</label>
            <input
              type="email"
              defaultValue="staff@pharmacy.com"
              className="w-full border border-slate-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              placeholder="you@pharmacy.com"
            />
          </div>
          <div>
            <label className="block text-[12px] font-medium text-slate-600 mb-1.5">Password</label>
            <input
              type="password"
              defaultValue="password"
              className="w-full border border-slate-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              placeholder="••••••••"
            />
          </div>
        </div>

        <button
          type="submit"
          className="w-full mt-6 py-2.5 bg-gradient-to-r from-teal-600 to-teal-700 text-white text-[13px] font-medium rounded-lg hover:from-teal-700 hover:to-teal-800 transition-all flex items-center justify-center gap-2 shadow-sm shadow-teal-600/20"
        >
          Sign In
          <ArrowRight className="w-3.5 h-3.5" />
        </button>

        <p className="text-[11px] text-center text-slate-400 mt-4">
          Demo mode — click Sign In to access the platform
        </p>
      </form>

      {/* Footer */}
      <p className="text-[11px] text-center text-slate-400 mt-6">
        Secured with end-to-end encryption
      </p>
    </div>
  );
}
