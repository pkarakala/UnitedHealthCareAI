export default function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2.5 py-12">
      <div className="w-4 h-4 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
      {label && <span className="text-[13px] text-slate-400">{label}</span>}
    </div>
  );
}
