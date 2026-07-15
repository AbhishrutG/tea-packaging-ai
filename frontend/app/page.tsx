import Link from "next/link";
import { listSimulations, getSimulation } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { RadialGauge } from "@/components/RadialGauge";

const MATERIAL_COLOR: Record<string, string> = {
  paper: "badge-neutral",
  plastic: "badge-positive",
  metal: "badge-negative",
};

export const dynamic = "force-dynamic";

// This is a Server Component (default in Next.js App Router) -- the data
// fetching below runs on the SERVER before the page is sent to the browser,
// not in the user's browser. That means no loading spinner is needed here;
// the page arrives with real data already in it.
export default async function DashboardPage() {
  let simulations: Awaited<ReturnType<typeof listSimulations>> = [];
  let fetchError: string | null = null;

  try {
    simulations = await listSimulations(10);
  } catch {
    fetchError = "Could not reach the API. Is the backend running on port 8000?";
  }

  const details = fetchError
    ? []
    : await Promise.all(
        simulations.map((s) => getSimulation(s.id).catch(() => null))
      );

  const validResults = details.filter((d) => d && d.result) as NonNullable<
    (typeof details)[number]
  >[];

  const totalSavings = validResults.reduce(
    (sum, d) => sum + (d.result!.current.total_cost_usd - d.result!.ai.total_cost_usd),
    0
  );

  const avgUtilization =
    validResults.length > 0
      ? validResults.reduce(
          (sum, d) => sum + Number(d.result!.ai.container.container_utilization),
          0
        ) / validResults.length
      : 0;

  return (
    <div className="px-10 py-8 max-w-6xl">
      <header className="mb-8">
        <h1 className="font-display text-2xl font-bold text-paper">Dashboard</h1>
        <p className="text-muted text-sm mt-1">
          Overview of packaging optimization runs across your shipments.
        </p>
      </header>

      {fetchError && (
        <div className="mb-6 rounded-md border border-alert/40 bg-alert/10 px-4 py-3 text-sm text-alert">
          {fetchError}
        </div>
      )}

      <div className="grid grid-cols-3 gap-4 mb-10">
        <StatCard label="Total Simulations" value={String(simulations.length)} />
        <StatCard
          label="Total Savings"
          value={`$${totalSavings.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
          sublabel="AI vs current packaging, recent runs"
          accent="teal"
        />
        <div className="card card-hover relative overflow-hidden px-5 py-4 flex items-center justify-between">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-copper opacity-70" />
          <div>
            <div className="text-xs uppercase tracking-wide text-muted mb-2">
              Avg Container Utilization
            </div>
            <div className="text-xs text-muted">Across AI-optimized recommendations</div>
          </div>
          <RadialGauge ratio={avgUtilization} size={64} stroke={7} />
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-bold text-paper">Recent Simulations</h2>
        <Link href="/simulation/new" className="text-sm text-copper hover:underline">
          + New Simulation
        </Link>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-2 text-muted text-xs uppercase tracking-wide">
              <th className="text-left px-4 py-3 font-medium">ID</th>
              <th className="text-left px-4 py-3 font-medium">Shipment Qty</th>
              <th className="text-left px-4 py-3 font-medium">Material</th>
              <th className="text-left px-4 py-3 font-medium">Created</th>
              <th className="text-right px-4 py-3 font-medium">Total Cost (AI)</th>
              <th className="text-right px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {simulations.length === 0 && !fetchError && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted">
                  No simulations yet. Run your first optimization to see it here.
                </td>
              </tr>
            )}
            {simulations.map((sim, i) => {
              const detail = details[i];
              return (
                <tr
                  key={sim.id}
                  className="border-t border-border hover:bg-surface-2 transition-colors"
                >
                  <td className="px-4 py-3 font-mono-data text-copper">#{sim.id}</td>
                  <td className="px-4 py-3 font-mono-data">
                    {sim.shipment_quantity.toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`badge ${MATERIAL_COLOR[sim.packaging_material] ?? "badge-neutral"} capitalize`}
                    >
                      {sim.packaging_material}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {new Date(sim.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 font-mono-data text-right">
                    {detail?.result
                      ? `$${detail.result.ai.total_cost_usd.toLocaleString()}`
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link href={`/simulation/${sim.id}`} className="text-copper text-xs hover:underline">
                      View →
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
