import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { MapMode, SelectionState } from "@/types";

interface AppContextValue extends SelectionState {
  setMapMode: (mode: MapMode) => void;
  selectState: (state: string | null) => void;
  selectDistrict: (id: number | null, name: string | null, state?: string) => void;
  selectConstituency: (
    id: number | null,
    name: string | null,
    state?: string,
  ) => void;
  setHighlightGeoId: (id: string | null) => void;
  commandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;
  resetSelection: () => void;
}

const defaultSelection: SelectionState = {
  mapMode: "state",
  selectedState: null,
  selectedDistrictId: null,
  selectedDistrictName: null,
  selectedConstituencyId: null,
  selectedConstituencyName: null,
  highlightGeoId: null,
};

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [selection, setSelection] = useState<SelectionState>(defaultSelection);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  const setMapMode = useCallback((mapMode: MapMode) => {
    setSelection((s) => ({ ...s, mapMode }));
  }, []);

  const selectState = useCallback((state: string | null) => {
    setSelection((s) => ({
      ...s,
      selectedState: state,
      selectedDistrictId: null,
      selectedDistrictName: null,
      selectedConstituencyId: null,
      selectedConstituencyName: null,
      mapMode: state ? "district" : "state",
    }));
  }, []);

  const selectDistrict = useCallback(
    (id: number | null, name: string | null, state?: string) => {
      setSelection((s) => ({
        ...s,
        selectedDistrictId: id,
        selectedDistrictName: name,
        selectedState: state ?? s.selectedState,
        selectedConstituencyId: null,
        selectedConstituencyName: null,
      }));
    },
    [],
  );

  const selectConstituency = useCallback(
    (id: number | null, name: string | null, state?: string) => {
      setSelection((s) => ({
        ...s,
        selectedConstituencyId: id,
        selectedConstituencyName: name,
        selectedState: state ?? s.selectedState,
        mapMode: "constituency",
      }));
    },
    [],
  );

  const setHighlightGeoId = useCallback((highlightGeoId: string | null) => {
    setSelection((s) => ({ ...s, highlightGeoId }));
  }, []);

  const resetSelection = useCallback(() => {
    setSelection(defaultSelection);
  }, []);

  const value = useMemo(
    () => ({
      ...selection,
      setMapMode,
      selectState,
      selectDistrict,
      selectConstituency,
      setHighlightGeoId,
      commandPaletteOpen,
      setCommandPaletteOpen,
      resetSelection,
    }),
    [
      selection,
      setMapMode,
      selectState,
      selectDistrict,
      selectConstituency,
      setHighlightGeoId,
      commandPaletteOpen,
      resetSelection,
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
