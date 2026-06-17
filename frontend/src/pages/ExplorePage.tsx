import { useMemo, useState } from "react";
import { ConstituencyPanel } from "@/components/ConstituencyPanel";
import { IndiaMap } from "@/components/IndiaMap";
import { SearchBox } from "@/components/SearchBox";
import { EmptyState, PageError, PageLoader } from "@/components/Layout";
import { APP_DESCRIPTION, MAP_COLOR_MODES, type MapColorMode } from "@/lib/constants";
import { useDashboardData } from "@/context/DataContext";
import type { ConstituencyRecord } from "@/lib/data";

export function ExplorePage() {
  const { data, isLoading, isError, error } = useDashboardData();
  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState<string | null>(null);
  const [colorMode, setColorMode] = useState<MapColorMode>("winner_2024");
  const [selected, setSelected] = useState<ConstituencyRecord | null>(null);

  const states = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.constituencies.map((c) => c.state))].sort();
  }, [data]);

  if (isLoading) return <PageLoader />;
  if (isError || !data) return <PageError message={error?.message} />;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Explore</h1>
        <p className="mt-1 max-w-3xl text-sm text-muted">{APP_DESCRIPTION}</p>
        <p className="mt-1 text-sm text-muted">
          {data.coverageSummary.election_constituencies_total} constituencies ·{" "}
          {data.coverageSummary.constituencies_with_demographic_coverage} with demographic coverage
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-3">
          <div className="grid gap-3 md:grid-cols-3">
            <div className="md:col-span-2">
              <SearchBox
                constituencies={data.constituencies}
                value={search}
                onChange={setSearch}
                onSelect={(record) => {
                  setSelected(record);
                  setStateFilter(record.state);
                }}
              />
            </div>
            <select
              value={stateFilter || ""}
              onChange={(e) => setStateFilter(e.target.value || null)}
              className="rounded-lg border border-border bg-bg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/40"
            >
              <option value="">All states</option>
              {states.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-wrap gap-2">
            {MAP_COLOR_MODES.map((mode) => (
              <button
                key={mode.id}
                type="button"
                onClick={() => setColorMode(mode.id)}
                className={[
                  "rounded-full border px-3 py-1 text-xs",
                  colorMode === mode.id
                    ? "border-primary bg-primary/15 text-primary"
                    : "border-border text-muted hover:text-text",
                ].join(" ")}
              >
                {mode.label}
              </button>
            ))}
          </div>

          <IndiaMap
            data={data}
            colorMode={colorMode}
            stateFilter={stateFilter}
            selected={selected}
            onConstituencyClick={setSelected}
          />
        </div>

        <ConstituencyPanel record={selected} />
      </div>

      {data.constituencies.length === 0 ? (
        <EmptyState title="No constituencies loaded" body="Rebuild the frontend data bundle." />
      ) : null}
    </div>
  );
}
