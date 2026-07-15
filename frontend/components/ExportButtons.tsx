"use client";

import { useState } from "react";
import type { SimulationDetail } from "@/lib/api";
import { exportToPdf, exportToExcel } from "@/lib/export";

export function ExportButtons({ detail }: { detail: SimulationDetail }) {
  const [busy, setBusy] = useState<"pdf" | "excel" | null>(null);

  async function handle(kind: "pdf" | "excel") {
    setBusy(kind);
    try {
      if (kind === "pdf") await exportToPdf(detail);
      else await exportToExcel(detail);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex items-center gap-2 shrink-0">
      <button
        onClick={() => handle("pdf")}
        disabled={busy !== null}
        className="text-xs px-3 py-2 rounded-md border border-border text-muted hover:text-paper hover:border-copper transition-colors disabled:opacity-50"
      >
        {busy === "pdf" ? "Exporting…" : "Export PDF"}
      </button>
      <button
        onClick={() => handle("excel")}
        disabled={busy !== null}
        className="text-xs px-3 py-2 rounded-md border border-border text-muted hover:text-paper hover:border-teal transition-colors disabled:opacity-50"
      >
        {busy === "excel" ? "Exporting…" : "Export Excel"}
      </button>
    </div>
  );
}
