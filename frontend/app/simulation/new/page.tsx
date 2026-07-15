"use client";
// "use client" -- this page needs useState and onClick handlers, which only
// work in the BROWSER, not on the server. Marking a file "use client" tells
// Next.js to send this component's code to the browser and run it there,
// unlike page.tsx (the Dashboard) which ran entirely on the server.

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createSimulation } from "@/lib/api";

const MATERIALS = ["paper", "plastic", "metal"];
const SHAPES = ["square", "round"];
const SHIPMENT_TYPES = [
  { value: "total_weight", label: "Total Weight" },
  { value: "per_container", label: "Per Container" },
];

export default function NewSimulationPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    tea_density_g_cm3: 0.4,
    package_weight_g: 100,
    shipment_quantity: 50000,
    shipment_type: "total_weight",
    package_shape: "square",
    packaging_material: "paper",
    target_market: "",
  });

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const sim = await createSimulation({
        ...form,
        target_market: form.target_market || null,
      });
      router.push(`/simulation/${sim.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setSubmitting(false);
    }
  }

  return (
    <div className="px-10 py-8 max-w-2xl">
      <header className="mb-8">
        <h1 className="font-display text-2xl font-bold text-paper">New Simulation</h1>
        <p className="text-muted text-sm mt-1">
          Enter shipment details. The optimizer runs the full package → carton → pallet →
          container pipeline and compares it against a naive baseline.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Tea Density (g/cm³)">
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={form.tea_density_g_cm3}
              onChange={(e) => update("tea_density_g_cm3", Number(e.target.value))}
              className="input"
              required
            />
          </Field>

          <Field label="Package Weight (g)">
            <select
              value={form.package_weight_g}
              onChange={(e) => update("package_weight_g", Number(e.target.value))}
              className="input"
            >
              {[50, 100, 150, 200, 250, 500].map((w) => (
                <option key={w} value={w}>
                  {w} g
                </option>
              ))}
            </select>
          </Field>

          <Field label="Shipment Quantity">
            <input
              type="number"
              min="1"
              value={form.shipment_quantity}
              onChange={(e) => update("shipment_quantity", Number(e.target.value))}
              className="input"
              required
            />
          </Field>

          <Field label="Shipment Type">
            <select
              value={form.shipment_type}
              onChange={(e) => update("shipment_type", e.target.value)}
              className="input"
            >
              {SHIPMENT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Package Shape">
            <select
              value={form.package_shape}
              onChange={(e) => update("package_shape", e.target.value)}
              className="input capitalize"
            >
              {SHAPES.map((s) => (
                <option key={s} value={s} className="capitalize">
                  {s}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Packaging Material">
            <select
              value={form.packaging_material}
              onChange={(e) => update("packaging_material", e.target.value)}
              className="input capitalize"
            >
              {MATERIALS.map((m) => (
                <option key={m} value={m} className="capitalize">
                  {m}
                </option>
              ))}
            </select>
          </Field>

          <div className="col-span-2">
            <Field label="Target Market (optional)">
              <input
                type="text"
                placeholder="e.g. European Union"
                value={form.target_market}
                onChange={(e) => update("target_market", e.target.value)}
                className="input"
              />
            </Field>
          </div>
        </div>

        {error && (
          <div className="rounded-md border border-alert/40 bg-alert/10 px-4 py-3 text-sm text-alert">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="bg-copper text-ink font-medium px-5 py-2.5 rounded-md text-sm hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {submitting ? "Running optimization…" : "Run Optimization"}
        </button>
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-xs uppercase tracking-wide text-muted mb-1.5">
        {label}
      </span>
      {children}
    </label>
  );
}
