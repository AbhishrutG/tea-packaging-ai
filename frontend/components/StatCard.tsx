export function StatCard({
  label,
  value,
  sublabel,
  accent = "copper",
  icon,
}: {
  label: string;
  value: string;
  sublabel?: string;
  accent?: "copper" | "teal";
  icon?: React.ReactNode;
}) {
  const accentColor = accent === "teal" ? "text-teal" : "text-copper";
  const accentBg = accent === "teal" ? "bg-teal" : "bg-copper";
  return (
    <div className="card card-hover relative overflow-hidden px-5 py-4">
      <div className={`absolute top-0 left-0 right-0 h-[3px] ${accentBg} opacity-70`} />
      <div className="flex items-start justify-between">
        <div className="text-xs uppercase tracking-wide text-muted mb-2">{label}</div>
        {icon && <div className={`${accentColor} opacity-80`}>{icon}</div>}
      </div>
      <div className={`font-mono-data text-3xl font-semibold ${accentColor}`}>{value}</div>
      {sublabel && <div className="text-xs text-muted mt-1.5">{sublabel}</div>}
    </div>
  );
}
