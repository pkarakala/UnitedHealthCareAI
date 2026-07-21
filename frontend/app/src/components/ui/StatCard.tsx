import { TrendingUp, TrendingDown } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  icon?: React.ReactNode;
}

export default function StatCard({ title, value, subtitle, trend, icon }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 hover:shadow-md hover:shadow-slate-100 transition-all duration-200">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[12px] font-medium text-slate-500 uppercase tracking-wider">{title}</p>
          <p className="text-2xl font-bold text-slate-900 mt-1.5 tracking-tight">{value}</p>
          {subtitle && (
            <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
              {trend === "up" && <TrendingUp className="w-3 h-3 text-emerald-500" />}
              {trend === "down" && <TrendingDown className="w-3 h-3 text-red-500" />}
              {subtitle}
            </p>
          )}
        </div>
        {icon && (
          <div className="w-10 h-10 rounded-lg bg-slate-50 flex items-center justify-center">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
