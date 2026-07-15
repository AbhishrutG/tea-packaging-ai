/**
 * RadialGauge -- an SVG donut readout for a single 0-1 ratio.
 *
 * Used anywhere a percentage deserves more visual weight than a plain
 * number, e.g. average container utilization on the Dashboard.
 */
export function RadialGauge({
  ratio,
  size = 96,
  stroke = 10,
  color = "copper",
  label,
}: {
  ratio: number; // 0 to 1
  size?: number;
  stroke?: number;
  color?: "copper" | "teal";
  label?: string;
}) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.min(Math.max(ratio, 0), 1));
  const strokeColor = color === "teal" ? "var(--teal)" : "var(--copper)";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--surface-2)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="font-mono-data text-lg font-semibold text-paper">
          {(ratio * 100).toFixed(0)}%
        </span>
        {label && <span className="text-[9px] uppercase tracking-wide text-muted mt-0.5">{label}</span>}
      </div>
    </div>
  );
}
