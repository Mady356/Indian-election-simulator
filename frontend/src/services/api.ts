import { API_BASE } from "@/lib/constants";
import type {
  Constituency,
  ConstituencyDemographics,
  ConstituencyDetail,
  ConstituencyResults,
  District,
  DistrictDetail,
  SimulationRequest,
  SimulationResponse,
} from "@/types";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => fetchJson<{ status: string; database: string }>("/health"),

  districts: (params?: { state?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.state) q.set("state", params.state);
    if (params?.search) q.set("search", params.search);
    const qs = q.toString();
    return fetchJson<District[]>(`/districts${qs ? `?${qs}` : ""}`);
  },

  district: (id: number) => fetchJson<DistrictDetail>(`/districts/${id}`),

  constituencies: (params?: {
    state?: string;
    search?: string;
    party_winner?: string;
    year?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.state) q.set("state", params.state);
    if (params?.search) q.set("search", params.search);
    if (params?.party_winner) q.set("party_winner", params.party_winner);
    if (params?.year) q.set("year", String(params.year));
    const qs = q.toString();
    return fetchJson<Constituency[]>(`/constituencies${qs ? `?${qs}` : ""}`);
  },

  constituency: (id: number) =>
    fetchJson<ConstituencyDetail>(`/constituencies/${id}`),

  constituencyDemographics: (id: number) =>
    fetchJson<ConstituencyDemographics>(`/constituencies/${id}/demographics`),

  constituencyResults: (id: number) =>
    fetchJson<ConstituencyResults>(`/constituencies/${id}/results`),

  simulate: (body: SimulationRequest) =>
    fetch(`${API_BASE}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(async (res) => {
      if (!res.ok) throw new Error(`Simulation failed: ${res.status}`);
      return res.json() as Promise<SimulationResponse>;
    }),
};

export async function loadCsv(path: string): Promise<Record<string, string>[]> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}`);
  const text = await res.text();
  const { parseCsv } = await import("@/lib/utils");
  return parseCsv(text);
}
