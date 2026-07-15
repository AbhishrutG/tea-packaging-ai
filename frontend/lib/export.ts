/**
 * export.ts
 *
 * WHAT THIS FILE DOES (small why):
 * Turns a simulation's result data into a downloadable PDF or Excel file,
 * entirely in the browser (no server round-trip).
 *
 * WHY THIS MATTERS (big why):
 * The PDF's bonus features list "Export to PDF" and "Export to Excel" so a
 * logistics/procurement stakeholder can take the Current-vs-AI comparison
 * out of the app and share it. Doing this client-side keeps the backend
 * unchanged and the export instant.
 */

import type { SimulationDetail } from "@/lib/api";

type Result = NonNullable<SimulationDetail["result"]>;

const ROWS: {
  label: string;
  key: keyof Result["improvement_pct"];
  current: (r: Result) => string;
  ai: (r: Result) => string;
}[] = [
  {
    label: "Units per Carton",
    key: "units_per_carton",
    current: (r) => String(r.current.carton.units_per_carton),
    ai: (r) => String(r.ai.carton.units_per_carton),
  },
  {
    label: "Cartons per Pallet",
    key: "cartons_per_pallet",
    current: (r) => String(r.current.pallet.cartons_per_pallet),
    ai: (r) => String(r.ai.pallet.cartons_per_pallet),
  },
  {
    label: "Containers Required",
    key: "containers_required",
    current: (r) => String(r.current.container.containers_required),
    ai: (r) => String(r.ai.container.containers_required),
  },
  {
    label: "Container Utilization",
    key: "container_utilization",
    current: (r) => `${(Number(r.current.container.container_utilization) * 100).toFixed(1)}%`,
    ai: (r) => `${(Number(r.ai.container.container_utilization) * 100).toFixed(1)}%`,
  },
  {
    label: "Packaging Cost",
    key: "packaging_cost",
    current: (r) => `$${r.current.packaging_cost_usd.toLocaleString()}`,
    ai: (r) => `$${r.ai.packaging_cost_usd.toLocaleString()}`,
  },
  {
    label: "Freight Cost",
    key: "freight_cost",
    current: (r) => `$${Number(r.current.container.freight_cost_usd).toLocaleString()}`,
    ai: (r) => `$${Number(r.ai.container.freight_cost_usd).toLocaleString()}`,
  },
  {
    label: "Total Cost",
    key: "total_cost",
    current: (r) => `$${r.current.total_cost_usd.toLocaleString()}`,
    ai: (r) => `$${r.ai.total_cost_usd.toLocaleString()}`,
  },
];

function buildRows(detail: SimulationDetail) {
  const result = detail.result!;
  return ROWS.map((row) => ({
    Parameter: row.label,
    Current: row.current(result),
    AI: row.ai(result),
    "Improvement %": `${result.improvement_pct[row.key]}%`,
  }));
}

export async function exportToPdf(detail: SimulationDetail) {
  const { simulation } = detail;
  const result = detail.result;
  if (!result) return;

  const { jsPDF } = await import("jspdf");
  const autoTable = (await import("jspdf-autotable")).default;

  const doc = new jsPDF();

  doc.setFontSize(16);
  doc.text("Tea Packaging Optimization Report", 14, 18);

  doc.setFontSize(10);
  doc.setTextColor(100);
  doc.text(
    `Simulation #${simulation.id} · ${simulation.shipment_quantity.toLocaleString()} units · ` +
      `${simulation.packaging_material} · ${simulation.package_shape}`,
    14,
    26
  );
  doc.text(`Generated ${new Date().toLocaleString()}`, 14, 32);

  const savings = result.current.total_cost_usd - result.ai.total_cost_usd;
  doc.setTextColor(0);
  doc.setFontSize(12);
  doc.text(`Total Cost Savings: $${savings.toLocaleString()}`, 14, 42);

  autoTable(doc, {
    startY: 50,
    head: [["Parameter", "Current", "AI", "Improvement"]],
    body: buildRows(detail).map((r) => [r.Parameter, r.Current, r.AI, r["Improvement %"]]),
    headStyles: { fillColor: [79, 169, 140] },
    styles: { fontSize: 9 },
  });

  doc.save(`simulation-${simulation.id}-report.pdf`);
}

export async function exportToExcel(detail: SimulationDetail) {
  const { simulation } = detail;
  if (!detail.result) return;

  const XLSX = await import("xlsx");

  const summarySheet = XLSX.utils.json_to_sheet([
    { Field: "Simulation ID", Value: simulation.id },
    { Field: "Shipment Quantity", Value: simulation.shipment_quantity },
    { Field: "Packaging Material", Value: simulation.packaging_material },
    { Field: "Package Shape", Value: simulation.package_shape },
    { Field: "Tea Density (g/cm3)", Value: simulation.tea_density_g_cm3 },
    { Field: "Created", Value: new Date(simulation.created_at).toLocaleString() },
  ]);

  const comparisonSheet = XLSX.utils.json_to_sheet(buildRows(detail));

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, summarySheet, "Simulation");
  XLSX.utils.book_append_sheet(workbook, comparisonSheet, "Current vs AI");

  XLSX.writeFile(workbook, `simulation-${simulation.id}-report.xlsx`);
}
