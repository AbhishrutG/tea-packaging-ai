import Link from "next/link";
import { getSimulation } from "@/lib/api";
import { UtilizationBar } from "@/components/UtilizationBar";
import { RadialGauge } from "@/components/RadialGauge";
import { DeltaBadge } from "@/components/DeltaBadge";
import { ExportButtons } from "@/components/ExportButtons";

export default async function SimulationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const detail = await getSimulation(Number(id));
  const { simulation, result } = detail;

  if (!result) {
    return (
      <div className="px-10 py-8">
        <p className="text-muted">No result found for this simulation.</p>
      </div>
    );
  }

  const { ai, current, improvement_pct, all_container_options } = result;

  return (
    <div className="px-10 py-8 max-w-5xl">
      <header className="mb-8 flex items-start justify-between gap-6">
        <div>
          <Link href="/simulation" className="text-xs text-muted hover:text-copper">
            ← All simulations
          </Link>
          <h1 className="font-display text-2xl font-bold text-paper mt-2">
            Simulation #{simulation.id}
          </h1>
          <p className="text-muted text-sm mt-1">
            {simulation.shipment_quantity.toLocaleString()} units · {simulation.tea_density_g_cm3}{" "}
            g/cm³ density · {simulation.package_weight_g}g per package · {simulation.packaging_material}
          </p>
        </div>
        <div className="card flex items-center gap-4 px-5 py-3 shrink-0">
          <RadialGauge ratio={Number(ai.container.container_utilization)} size={56} stroke={6} />
          <div>
            <div className="text-xs uppercase tracking-wide text-muted">Total Cost Savings</div>
            <div className="font-mono-data text-xl font-semibold text-teal">
              ${(current.total_cost_usd - ai.total_cost_usd).toLocaleString()}
            </div>
            <DeltaBadge pct={improvement_pct.total_cost} />
          </div>
        </div>
        <ExportButtons detail={detail} />
      </header>

      {/* ---- AI RECOMMENDATION ---- */}
      <section className="mb-10">
        <h2 className="font-display font-bold text-paper mb-4">AI Recommendation</h2>
        <div className="grid grid-cols-4 gap-3 relative">
          <PipelineCard title="Package" step={1}>
            <Stat label="Dimensions" value={`${ai.package.length_cm}×${ai.package.width_cm}×${ai.package.height_cm} cm`} />
            <Stat label="Surface Area" value={`${ai.package.surface_area_cm2} cm²`} />
          </PipelineCard>
          <PipelineCard title="Carton" step={2}>
            <Stat label="Size" value={`${ai.carton.carton_length_cm}×${ai.carton.carton_width_cm}×${ai.carton.carton_height_cm} cm`} />
            <Stat label="Units/Carton" value={String(ai.carton.units_per_carton)} />
            <Stat label="Board Grade" value={String(ai.carton.board_grade)} />
          </PipelineCard>
          <PipelineCard title="Pallet" step={3}>
            <Stat label="Cartons/Pallet" value={String(ai.pallet.cartons_per_pallet)} />
            <Stat label="Layers" value={String(ai.pallet.layers)} />
            <Stat label="Height" value={`${ai.pallet.pallet_height_cm} cm`} />
          </PipelineCard>
          <PipelineCard title="Container" step={4} last>
            <Stat label="Type" value={String(ai.container.container_type)} />
            <Stat label="Containers Needed" value={String(ai.container.containers_required)} />
            <Stat label="Freight Cost" value={`$${ai.container.freight_cost_usd}`} />
          </PipelineCard>
        </div>
      </section>

      {/* ---- CONTAINER COMPARISON ---- */}
      <section className="mb-10">
        <h2 className="font-display font-bold text-paper mb-4">
          Container Comparison — 20GP / 40GP / 40HC
        </h2>
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface text-muted text-xs uppercase tracking-wide">
                <th className="text-left px-4 py-3 font-medium">Type</th>
                <th className="text-left px-4 py-3 font-medium">Containers Required</th>
                <th className="text-left px-4 py-3 font-medium">Utilization</th>
                <th className="text-right px-4 py-3 font-medium">Freight Cost</th>
              </tr>
            </thead>
            <tbody>
              {all_container_options.map((opt) => {
                const isRecommended = opt.container_type === ai.container.container_type;
                return (
                  <tr
                    key={String(opt.container_type)}
                    className={`border-t border-border ${isRecommended ? "bg-copper/10" : ""}`}
                  >
                    <td className="px-4 py-3 font-mono-data">
                      {opt.container_type}
                      {isRecommended && (
                        <span className="ml-2 text-[10px] uppercase tracking-wide text-copper border border-copper/40 rounded px-1.5 py-0.5">
                          Recommended
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono-data">{opt.containers_required}</td>
                    <td className="px-4 py-3 w-52">
                      <UtilizationBar ratio={Number(opt.container_utilization)} segments={16} />
                    </td>
                    <td className="px-4 py-3 font-mono-data text-right">
                      ${Number(opt.freight_cost_usd).toLocaleString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* ---- CURRENT VS AI ---- */}
      <section className="mb-10">
        <h2 className="font-display font-bold text-paper mb-4">Current vs AI Comparison</h2>
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface text-muted text-xs uppercase tracking-wide">
                <th className="text-left px-4 py-3 font-medium">Parameter</th>
                <th className="text-right px-4 py-3 font-medium">Current</th>
                <th className="text-right px-4 py-3 font-medium">AI</th>
                <th className="text-right px-4 py-3 font-medium">Improvement</th>
              </tr>
            </thead>
            <tbody>
              <ComparisonRow
                label="Units per Carton"
                currentVal={String(current.carton.units_per_carton)}
                aiVal={String(ai.carton.units_per_carton)}
                pct={improvement_pct.units_per_carton}
              />
              <ComparisonRow
                label="Cartons per Pallet"
                currentVal={String(current.pallet.cartons_per_pallet)}
                aiVal={String(ai.pallet.cartons_per_pallet)}
                pct={improvement_pct.cartons_per_pallet}
                note="Fewer, larger cartons — see notes"
              />
              <ComparisonRow
                label="Containers Required"
                currentVal={String(current.container.containers_required)}
                aiVal={String(ai.container.containers_required)}
                pct={improvement_pct.containers_required}
              />
              <ComparisonRow
                label="Container Utilization"
                currentVal={`${(Number(current.container.container_utilization) * 100).toFixed(1)}%`}
                aiVal={`${(Number(ai.container.container_utilization) * 100).toFixed(1)}%`}
                pct={improvement_pct.container_utilization}
              />
              <ComparisonRow
                label="Packaging Cost"
                currentVal={`$${current.packaging_cost_usd.toLocaleString()}`}
                aiVal={`$${ai.packaging_cost_usd.toLocaleString()}`}
                pct={improvement_pct.packaging_cost}
              />
              <ComparisonRow
                label="Freight Cost"
                currentVal={`$${Number(current.container.freight_cost_usd).toLocaleString()}`}
                aiVal={`$${Number(ai.container.freight_cost_usd).toLocaleString()}`}
                pct={improvement_pct.freight_cost}
              />
              <ComparisonRow
                label="Total Cost"
                currentVal={`$${current.total_cost_usd.toLocaleString()}`}
                aiVal={`$${ai.total_cost_usd.toLocaleString()}`}
                pct={improvement_pct.total_cost}
                emphasize
              />
            </tbody>
          </table>
        </div>
        <p className="text-xs text-muted mt-3">
          &ldquo;Current&rdquo; is generated from a naive (unoptimized) run of the same pipeline —
          not a hardcoded estimate — so every improvement percentage above is derived from real
          logic. See documentation for details on how the baseline is constructed.
        </p>
      </section>
    </div>
  );
}

function PipelineCard({
  title,
  step,
  last,
  children,
}: {
  title: string;
  step: number;
  last?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="card card-hover relative p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="font-mono-data text-[10px] w-5 h-5 rounded-full bg-teal-soft text-teal border border-teal/40 flex items-center justify-center">
          {step}
        </span>
        <div className="text-xs uppercase tracking-wide text-teal">{title}</div>
      </div>
      <div className="space-y-2">{children}</div>
      {!last && (
        <div className="hidden md:block absolute top-1/2 -right-3 -translate-y-1/2 text-teal/50 text-lg z-10">
          →
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] text-muted">{label}</div>
      <div className="font-mono-data text-sm text-paper">{value}</div>
    </div>
  );
}

function ComparisonRow({
  label,
  currentVal,
  aiVal,
  pct,
  note,
  emphasize,
}: {
  label: string;
  currentVal: string;
  aiVal: string;
  pct: number;
  note?: string;
  emphasize?: boolean;
}) {
  return (
    <tr className={`border-t border-border ${emphasize ? "bg-surface-2" : ""}`}>
      <td className="px-4 py-3">
        <span className={emphasize ? "font-medium text-paper" : "text-paper"}>{label}</span>
        {note && <div className="text-[11px] text-muted mt-0.5">{note}</div>}
      </td>
      <td className="px-4 py-3 font-mono-data text-right text-muted">{currentVal}</td>
      <td className="px-4 py-3 font-mono-data text-right text-paper">{aiVal}</td>
      <td className="px-4 py-3 text-right">
        <DeltaBadge pct={pct} />
      </td>
    </tr>
  );
}
