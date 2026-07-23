"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ClipboardList,
  PlusCircle,
  Users,
  Scale,
  MessageSquare,
  BarChart3,
  Settings,
  Activity,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Prior Auths", href: "/prior-auths", icon: ClipboardList },
  { name: "New Intake", href: "/prescriptions/intake", icon: PlusCircle },
  { name: "Patients", href: "/patients", icon: Users },
  { name: "Appeals", href: "/appeals", icon: Scale },
  { name: "Communications", href: "/communications", icon: MessageSquare },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-[240px] bg-[#0f172a] text-white min-h-screen flex flex-col fixed left-0 top-0 z-50">
      <div className="px-5 py-5 border-b border-white/5">
        <Link href="/dashboard" className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 rounded-lg flex items-center justify-center">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-[14px] font-semibold tracking-tight">
              USA<span className="text-teal-400">Healthcare</span>
            </h1>
            <p className="text-[10px] text-slate-500 -mt-0.5 tracking-wide uppercase">
              Prior Auth Platform
            </p>
          </div>
        </Link>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navigation.map((item) => {
          const isActive = pathname?.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150 ${
                isActive
                  ? "bg-teal-500/10 text-teal-400"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
              }`}
            >
              <Icon className={`w-[16px] h-[16px] ${isActive ? "text-teal-400" : "text-slate-500"}`} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="px-5 pb-4 text-[10px] text-slate-600">
        v1.0.0
      </div>
    </aside>
  );
}
