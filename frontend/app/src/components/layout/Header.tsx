"use client";

import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { clearToken } from "@/lib/auth";

export default function Header({ title }: { title: string }) {
  const router = useRouter();
  const [user, setUser] = useState<{ full_name: string | null; email: string } | null>(null);

  useEffect(() => {
    api.auth.me().then(setUser).catch(() => {});
  }, []);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  const initials = user?.full_name
    ? user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : user?.email?.slice(0, 2).toUpperCase() ?? "";

  return (
    <header className="h-14 border-b border-slate-200/80 bg-white/80 backdrop-blur-sm flex items-center justify-between px-6 sticky top-0 z-40">
      <h2 className="text-[15px] font-semibold text-slate-900 tracking-tight">{title}</h2>
      {user && (
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-slate-100 rounded-full flex items-center justify-center text-[11px] font-semibold text-slate-600">
              {initials}
            </div>
            <span className="text-[12px] text-slate-500 hidden sm:block">
              {user.full_name || user.email}
            </span>
          </div>
          <button
            onClick={handleLogout}
            aria-label="Sign out"
            title="Sign out"
            className="w-7 h-7 rounded-md hover:bg-slate-100 flex items-center justify-center transition-colors"
          >
            <LogOut className="w-3.5 h-3.5 text-slate-400" />
          </button>
        </div>
      )}
    </header>
  );
}
