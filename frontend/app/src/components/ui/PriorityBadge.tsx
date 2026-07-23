const priorityConfig: Record<string, { label: string; className: string }> = {
  high: { label: "High", className: "bg-red-50 text-red-600" },
  medium: { label: "Med", className: "bg-amber-50 text-amber-600" },
  low: { label: "Low", className: "bg-slate-50 text-slate-500" },
};

function getPriorityLevel(priority: number): "high" | "medium" | "low" {
  if (priority <= 3) return "high";
  if (priority <= 6) return "medium";
  return "low";
}

export default function PriorityBadge({ priority }: { priority: number }) {
  const level = getPriorityLevel(priority);
  const config = priorityConfig[level];
  return (
    <span className={`inline-flex items-center justify-center px-2 py-0.5 rounded-md text-[11px] font-semibold ${config.className}`}>
      {config.label}
    </span>
  );
}
