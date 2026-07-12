"use client";

export default function Header({ title }: { title: string }) {
  return (
    <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-6">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      <div className="flex items-center gap-4">
        <span className="inline-flex items-center gap-1.5 text-sm text-emerald-600">
          <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          System Online
        </span>
      </div>
    </header>
  );
}
