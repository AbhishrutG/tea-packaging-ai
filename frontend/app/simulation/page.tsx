import Link from "next/link";
import { listSimulations } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HistoryPage() {
  let simulations: Awaited<ReturnType<typeof listSimulations>> = [];
  let fetchError: string | null = null;

  try {
    simulations = await listSimulations(50);
  } catch {
    fetchError = "Could not reach the API. Is the backend running on port 8000?";
  }

  return (
    <div className="px-10 py-8 max-w-5xl">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-paper">History</h1>
          <p className="text-muted text-sm mt-1">All optimization runs, most recent first.</p>
        </div>
        <Link
          href="/simulation/new"
          className="bg-copper text-ink font-medium px-4 py-2 rounded-md text-sm hover:opacity-90 transition-opacity"
        >
          + New Simulation
        </Link>
      </header>

      {fetchError && (
        <div className="mb-6 rounded-md border border-alert/40 bg-alert/10 px-4 py-3 text-sm text-alert">
          {fetchError}
        </div>
      )}

      <div className="space-y-2">
        {simulations.map((sim) => (
          <Link
            key={sim.id}
            href={`/simulation/${sim.id}`}
            className="flex items-center justify-between border border-border rounded-lg px-5 py-4 hover:bg-surface transition-colors"
          >
            <div className="flex items-center gap-6">
              <span className="font-mono-data text-copper">#{sim.id}</span>
              <div>
                <div className="text-sm text-paper">
                  {sim.shipment_quantity.toLocaleString()} units · {sim.packaging_material} ·{" "}
                  {sim.package_shape}
                </div>
                <div className="text-xs text-muted mt-0.5">
                  density {sim.tea_density_g_cm3} g/cm³, {sim.package_weight_g}g/pkg
                  {sim.target_market ? ` · ${sim.target_market}` : ""}
                </div>
              </div>
            </div>
            <span className="text-xs text-muted">
              {new Date(sim.created_at).toLocaleString()}
            </span>
          </Link>
        ))}

        {simulations.length === 0 && !fetchError && (
          <div className="text-center text-muted py-12 border border-dashed border-border rounded-lg">
            No simulations yet.
          </div>
        )}
      </div>
    </div>
  );
}
