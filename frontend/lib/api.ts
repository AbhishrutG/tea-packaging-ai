/**
 * api.ts
 *
 * WHAT THIS FILE DOES (small why):
 * A small wrapper around `fetch` for every backend endpoint. Instead of
 * writing `fetch("http://...")` scattered across every page, every page
 * imports functions from here (e.g. `createSimulation(input)`).
 *
 * WHY THIS MATTERS (big why):
 * If the backend URL changes, or we need to add auth headers later, we
 * change it in ONE place instead of hunting through every page. This is
 * the same "keep one job in one place" idea as services/ on the backend --
 * here it's "keep all network calls in one place" on the frontend.
 */

// Server-side code (SSR/route handlers) runs inside the Docker container,
// where "localhost" refers to the frontend container itself, not the
// backend container. It must use the backend's Docker network name instead.
// Browser code runs on the host machine, where "localhost" correctly
// reaches the backend's published port.
const API_BASE =
  typeof window === "undefined"
    ? process.env.API_URL_INTERNAL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
    : process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface SimulationInput {
  tea_density_g_cm3: number;
  package_weight_g: number;
  shipment_quantity: number;
  shipment_type?: string;
  package_shape?: string;
  packaging_material?: string;
  target_market?: string | null;
}

export interface Simulation {
  id: number;
  tea_density_g_cm3: number;
  package_weight_g: number;
  shipment_quantity: number;
  shipment_type: string;
  package_shape: string;
  packaging_material: string;
  target_market: string | null;
  created_at: string;
}

export interface PipelineSnapshot {
  package: Record<string, number | string>;
  carton: Record<string, number | string>;
  pallet: Record<string, number | string>;
  container: Record<string, number | string>;
  packaging_cost_usd: number;
  total_cost_usd: number;
}

export interface SimulationDetail {
  simulation: Simulation;
  result: {
    ai: PipelineSnapshot;
    current: PipelineSnapshot;
    improvement_pct: Record<string, number>;
    all_container_options: Record<string, number | string>[];
  } | null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status} on ${path}: ${body}`);
  }
  return res.json();
}

export function createSimulation(input: SimulationInput) {
  return request<Simulation>("/simulation", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listSimulations(limit = 20) {
  return request<Simulation[]>(`/simulation?limit=${limit}`);
}

export function getSimulation(id: number) {
  return request<SimulationDetail>(`/simulation/${id}`);
}
