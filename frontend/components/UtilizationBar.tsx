/**
 * UtilizationBar -- the "signature element" of this UI.
 *
 * Renders container/carton fill percentage as a row of discrete blocks,
 * like a stack of crates loaded into a hold -- rather than a generic
 * rounded progress bar, this reads visually as "cargo space," which is
 * literally the subject of the app.
 */
export function UtilizationBar({
  ratio,
  segments = 20,
  color = "copper",
}: {
  ratio: number; // 0 to 1
  segments?: number;
  color?: "copper" | "teal";
}) {
  const filled = Math.round(ratio * segments);
  const barColor = color === "teal" ? "bg-teal" : "bg-copper";

  return (
    <div className="flex items-center gap-3">
      <div className="flex gap-[3px] flex-1">
        {Array.from({ length: segments }).map((_, i) => (
          <div
            key={i}
            className={`h-4 flex-1 rounded-[1px] ${
              i < filled ? barColor : "bg-surface-2"
            }`}
          />
        ))}
      </div>
      <span className="font-mono-data text-sm text-paper w-12 text-right">
        {(ratio * 100).toFixed(1)}%
      </span>
    </div>
  );
}
