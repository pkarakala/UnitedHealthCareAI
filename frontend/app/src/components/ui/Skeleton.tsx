interface SkeletonRowProps {
  columns: number;
  rows?: number;
}

export default function SkeletonRows({ columns, rows = 5 }: SkeletonRowProps) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i} className="animate-pulse">
          {Array.from({ length: columns }).map((_, j) => (
            <td key={j} className="px-5 py-3">
              <div className="h-4 bg-slate-100 rounded w-3/4" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}
