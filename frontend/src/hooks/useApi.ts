import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

export function useDistricts(params?: { state?: string; search?: string }) {
  return useQuery({
    queryKey: ["districts", params],
    queryFn: () => api.districts(params),
    staleTime: 5 * 60 * 1000,
  });
}

export function useDistrict(id: number | null) {
  return useQuery({
    queryKey: ["district", id],
    queryFn: () => api.district(id!),
    enabled: id != null,
  });
}

export function useConstituencies(params?: {
  state?: string;
  search?: string;
  party_winner?: string;
  year?: number;
}) {
  return useQuery({
    queryKey: ["constituencies", params],
    queryFn: () => api.constituencies(params),
    staleTime: 5 * 60 * 1000,
  });
}

export function useConstituency(id: number | null) {
  return useQuery({
    queryKey: ["constituency", id],
    queryFn: () => api.constituency(id!),
    enabled: id != null,
  });
}

export function useConstituencyDemographics(id: number | null) {
  return useQuery({
    queryKey: ["constituency-demographics", id],
    queryFn: () => api.constituencyDemographics(id!),
    enabled: id != null,
    retry: false,
  });
}

export function useConstituencyResults(id: number | null) {
  return useQuery({
    queryKey: ["constituency-results", id],
    queryFn: () => api.constituencyResults(id!),
    enabled: id != null,
    retry: false,
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
    retry: 1,
    refetchInterval: 30000,
  });
}
