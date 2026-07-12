"use client";

import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    router.push("/dashboard");
  }

  return (
    <div className="w-full max-w-md mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          USA<span className="text-emerald-600">Healthcare</span>.AI
        </h1>
        <p className="text-sm text-slate-500 mt-2">Prior Authorization Platform</p>
      </div>

      <form onSubmit={handleLogin} className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
          <input
            type="email"
            defaultValue="staff@pharmacy.com"
            className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm"
            placeholder="you@pharmacy.com"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
          <input
            type="password"
            defaultValue="password"
            className="w-full border border-slate-300 rounded-lg px-3 py-2.5 text-sm"
            placeholder="••••••••"
          />
        </div>
        <button
          type="submit"
          className="w-full py-2.5 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors"
        >
          Sign In
        </button>
        <p className="text-xs text-center text-slate-400">
          Demo mode — click Sign In to continue
        </p>
      </form>
    </div>
  );
}
