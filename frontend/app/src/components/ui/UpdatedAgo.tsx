"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

interface UpdatedAgoProps {
  lastUpdated: Date | null;
  onRefresh?: () => void;
}

export default function UpdatedAgo({ lastUpdated, onRefresh }: UpdatedAgoProps) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 5_000);
    return () => clearInterval(t);
  }, []);

  if (!lastUpdated) return null;

  const seconds = Math.floor((now - lastUpdated.getTime()) / 1000);
  const label = seconds < 10 ? "just now" : seconds < 60 ? `${seconds}s ago` : `${Math.floor(seconds / 60)}m ago`;

  return (
    <div className="flex items-center gap-2 text-[11px] text-slate-500">
      <span>Updated {label}</span>
      {onRefresh && (
        <button
          onClick={onRefresh}
          className="hover:text-slate-600 transition-colors"
          aria-label="Refresh"
        >
          <RefreshCw className="w-3 h-3" />
        </button>
      )}
    </div>
  );
}
