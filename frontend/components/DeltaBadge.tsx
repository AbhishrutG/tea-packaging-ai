export function DeltaBadge({ pct }: { pct: number }) {
  const positive = pct > 0;
  const flat = pct === 0;
  const cls = flat ? "badge-neutral" : positive ? "badge-positive" : "badge-negative";
  return (
    <span className={`badge ${cls}`}>
      {flat ? "" : positive ? "▲" : "▼"} {positive ? "+" : ""}
      {pct}%
    </span>
  );
}
