"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: "📊" },
  { name: "Prior Auths", href: "/prior-auths", icon: "📋" },
  { name: "New Intake", href: "/prescriptions/intake", icon: "➕" },
  { name: "Patients", href: "/patients", icon: "👤" },
  { name: "Appeals", href: "/appeals", icon: "⚖️" },
  { name: "Communications", href: "/communications", icon: "💬" },
  { name: "Analytics", href: "/analytics", icon: "📈" },
  { name: "Settings", href: "/settings", icon: "⚙️" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 text-white min-h-screen p-4 fixed left-0 top-0">
      <div className="mb-8">
        <h1 className="text-xl font-bold tracking-tight">
          USA<span className="text-emerald-400">Healthcare</span>.AI
        </h1>
        <p className="text-xs text-slate-400 mt-1">Prior Auth Platform</p>
      </div>

      <nav className="space-y-1">
        {navigation.map((item) => {
          const isActive = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-emerald-600/20 text-emerald-400 font-medium"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-4 left-4 right-4">
        <div className="bg-slate-800 rounded-lg p-3">
          <p className="text-xs text-slate-400">Logged in as</p>
          <p className="text-sm font-medium">Pharmacy Staff</p>
        </div>
      </div>
    </aside>
  );
}
