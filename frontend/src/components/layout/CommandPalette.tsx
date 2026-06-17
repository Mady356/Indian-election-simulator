import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MapPin, Search, Vote } from "lucide-react";
import clsx from "clsx";
import { useApp } from "@/context/AppContext";
import { useConstituencies, useDistricts } from "@/hooks/useApi";
import { normalizeKey, titleCase } from "@/lib/utils";
import type { SearchResult } from "@/types";

export function CommandPalette() {
  const navigate = useNavigate();
  const {
    commandPaletteOpen,
    setCommandPaletteOpen,
    selectState,
    selectDistrict,
    selectConstituency,
    setMapMode,
  } = useApp();
  const [query, setQuery] = useState("");

  const { data: districts = [] } = useDistricts();
  const { data: constituencies = [] } = useConstituencies();

  const results = useMemo(() => {
    if (!query.trim()) return [];
    const q = normalizeKey(query);
    const items: SearchResult[] = [];

    const states = new Set<string>();
    districts.forEach((d) => states.add(d.state));
    constituencies.forEach((c) => states.add(c.state));

    states.forEach((state) => {
      if (normalizeKey(state).includes(q)) {
        items.push({
          type: "state",
          id: state,
          label: state,
          sublabel: "State / UT",
          state,
        });
      }
    });

    districts.forEach((d) => {
      if (
        normalizeKey(d.district).includes(q) ||
        normalizeKey(`${d.state} ${d.district}`).includes(q)
      ) {
        items.push({
          type: "district",
          id: d.id,
          label: d.district,
          sublabel: d.state,
          state: d.state,
        });
      }
    });

    constituencies.forEach((c) => {
      if (
        normalizeKey(c.constituency).includes(q) ||
        normalizeKey(`${c.state} ${c.constituency}`).includes(q)
      ) {
        items.push({
          type: "constituency",
          id: c.id,
          label: c.constituency,
          sublabel: c.state,
          state: c.state,
        });
      }
    });

    return items.slice(0, 12);
  }, [query, districts, constituencies]);

  const handleSelect = (item: SearchResult) => {
    setCommandPaletteOpen(false);
    setQuery("");
    navigate("/");

    if (item.type === "state") {
      selectState(item.label);
      setMapMode("district");
    } else if (item.type === "district") {
      selectState(item.state);
      selectDistrict(item.id as number, item.label, item.state);
      setMapMode("district");
    } else {
      selectState(item.state);
      selectConstituency(item.id as number, item.label, item.state);
      setMapMode("constituency");
    }
  };

  if (!commandPaletteOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-[15vh] backdrop-blur-sm animate-fade-in"
      onClick={() => setCommandPaletteOpen(false)}
    >
      <div
        className="glass w-full max-w-xl overflow-hidden rounded-2xl shadow-glow animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-border px-4 py-3">
          <Search className="h-5 w-5 text-muted" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search state, district, constituency..."
            className="flex-1 bg-transparent text-sm text-text outline-none placeholder:text-muted"
          />
          <kbd className="rounded border border-border px-1.5 py-0.5 text-[10px] text-muted">
            ESC
          </kbd>
        </div>
        <ul className="max-h-80 overflow-y-auto py-2">
          {results.length === 0 && query && (
            <li className="px-4 py-6 text-center text-sm text-muted">
              No results for &ldquo;{query}&rdquo;
            </li>
          )}
          {results.map((item) => (
            <li key={`${item.type}-${item.id}`}>
              <button
                type="button"
                onClick={() => handleSelect(item)}
                className="flex w-full items-center gap-3 px-4 py-2.5 text-left transition hover:bg-primary/10"
              >
                {item.type === "constituency" ? (
                  <Vote className="h-4 w-4 text-primary" />
                ) : (
                  <MapPin className="h-4 w-4 text-accent" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm font-medium text-text">
                    {titleCase(item.label)}
                  </p>
                  <p className="truncate text-xs text-muted">{item.sublabel}</p>
                </div>
                <span
                  className={clsx(
                    "rounded px-2 py-0.5 text-[10px] uppercase tracking-wide",
                    item.type === "constituency"
                      ? "bg-primary/15 text-primary"
                      : item.type === "district"
                        ? "bg-accent/15 text-accent"
                        : "bg-border text-muted",
                  )}
                >
                  {item.type}
                </span>
              </button>
            </li>
          ))}
          {!query && (
            <li className="px-4 py-6 text-center text-sm text-muted">
              Type to search Varanasi, Mumbai, Bihar...
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}
