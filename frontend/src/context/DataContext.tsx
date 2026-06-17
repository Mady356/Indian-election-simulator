import { createContext, useContext, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { loadDashboardData, type DashboardData } from "@/lib/data";

interface DataContextValue {
  data: DashboardData | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

const DataContext = createContext<DataContextValue | null>(null);

export function DataProvider({ children }: { children: ReactNode }) {
  const query = useQuery({
    queryKey: ["dashboard-data"],
    queryFn: loadDashboardData,
    staleTime: 5 * 60 * 1000,
  });

  return (
    <DataContext.Provider
      value={{
        data: query.data,
        isLoading: query.isLoading,
        isError: query.isError,
        error: query.error,
      }}
    >
      {children}
    </DataContext.Provider>
  );
}

export function useDashboardData() {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error("useDashboardData must be used within DataProvider");
  return ctx;
}
