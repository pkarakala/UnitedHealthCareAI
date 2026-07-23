"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const { access_token } = await api.auth.login(email, password);
      setToken(access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error && err.message !== "Unauthorized"
          ? err.message
          : "Invalid email or password"
      );
      setSubmitting(false);
    }
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
            <label htmlFor="email" className="block text-[12px] font-medium text-slate-600 mb-1.5">
              Email address
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              placeholder="you@pharmacy.com"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-[12px] font-medium text-slate-600 mb-1.5">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-slate-200 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              placeholder="••••••••"
            />
          </div>
        </div>

        {error && (
          <p role="alert" className="mt-4 text-[13px] text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full mt-6 py-2.5 bg-gradient-to-r from-teal-600 to-teal-700 text-white text-[13px] font-medium rounded-lg hover:from-teal-700 hover:to-teal-800 transition-all flex items-center justify-center gap-2 shadow-sm shadow-teal-600/20 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {submitting ? "Signing in…" : "Sign In"}
          {!submitting && <ArrowRight className="w-3.5 h-3.5" />}
        </button>
      </form>

      {/* Footer */}
      <p className="text-[11px] text-center text-slate-500 mt-6">
        Access restricted to authorized pharmacy staff
      </p>
    </div>
  );
}
