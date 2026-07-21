"use client";

import { Bell, Search } from "lucide-react";

export default function Header({ title }: { title: string }) {
  return (
    <header className="h-16 border-b border-slate-200/80 bg-white/80 backdrop-blur-sm flex items-center justify-between px-8 sticky top-0 z-40">
      <h2 className="text-[15px] font-semibold text-slate-900 tracking-tight">{title}</h2>
      <div className="flex items-center gap-3">
        <button className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-colors">
          <Search className="w-4 h-4 text-slate-500" />
        </button>
        <button className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center transition-colors relative">
          <Bell className="w-4 h-4 text-slate-500" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-teal-500 rounded-full" />
        </button>
        <div className="h-5 w-px bg-slate-200 mx-1" />
        <span className="inline-flex items-center gap-1.5 text-[12px] text-teal-600 font-medium bg-teal-50 px-2.5 py-1 rounded-full">
          <span className="w-1.5 h-1.5 bg-teal-500 rounded-full animate-pulse" />
          Online
        </span>
      </div>
    </header>
  );
}
