"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/auth";
import {
  LayoutDashboard,
  ClipboardList,
  PlusCircle,
  Users,
  Scale,
  MessageSquare,
  BarChart3,
  Settings,
  LogOut,
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
  const router = useRouter();

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  return (
    <aside className="w-[260px] bg-[#0f172a] text-white min-h-screen flex flex-col fixed left-0 top-0 z-50">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-white/5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 rounded-lg flex items-center justify-center">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-[15px] font-semibold tracking-tight">
              USA<span className="text-teal-400">Healthcare</span>
            </h1>
            <p className="text-[10px] text-slate-400 -mt-0.5 tracking-wide uppercase">
              Prior Auth Platform
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navigation.map((item) => {
          const isActive = pathname?.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-all duration-150 ${
                isActive
                  ? "bg-teal-500/10 text-teal-400 shadow-sm shadow-teal-500/5"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
              }`}
            >
              <Icon className={`w-[18px] h-[18px] ${isActive ? "text-teal-400" : "text-slate-500"}`} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* User Section */}
      <div className="px-3 pb-4 border-t border-white/5 pt-4">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 bg-gradient-to-br from-slate-600 to-slate-700 rounded-full flex items-center justify-center text-xs font-medium">
            PS
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[12px] font-medium text-slate-300 truncate">Pharmacy Staff</p>
            <p className="text-[10px] text-slate-500 truncate">staff@pharmacy.com</p>
          </div>
          <button onClick={handleLogout} aria-label="Sign out" title="Sign out">
            <LogOut className="w-4 h-4 text-slate-500 hover:text-slate-300 cursor-pointer transition-colors" />
          </button>
        </div>
      </div>
    </aside>
  );
}
