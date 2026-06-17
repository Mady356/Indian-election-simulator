import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { MetricCard } from "@/components/MetricCard";
import { PageError, PageLoader } from "@/components/Layout";
import { useDashboardData } from "@/context/DataContext";
import { nationalSeatTotals } from "@/lib/data";
import { formatShare, formatSwing } from "@/lib/format";
import type { SwingRow } from "@/lib/data";

function SwingTable({ title, rows }: { title: string; rows: SwingRow[] }) {
  if (!rows?.length) return null;
  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="border-b border-border px-4 py-3 font-medium">{title}</div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-bg/50 text-left text-xs uppercase text-muted">
            <tr>
              <th className="px-4 py-2">#</th>
              <th className="px-4 py-2">Constituency</th>
              <th className="px-4 py-2">State</th>
              <th className="px-4 py-2">BJP swing</th>
              <th className="px-4 py-2">INC swing</th>
              <th className="px-4 py-2">2024 winner</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={`${row.state}-${row.constituency}-${idx}`} className="border-t border-border/60">
                <td className="px-4 py-2 text-muted">{row.rank ?? idx + 1}</td>
                <td className="px-4 py-2">{row.constituency}</td>
                <td className="px-4 py-2 text-muted">{row.state}</td>
                <td className="px-4 py-2">{formatSwing(row.bjp_swing_2019_2024)}</td>
                <td className="px-4 py-2">{formatSwing(row.inc_swing_2019_2024)}</td>
                <td className="px-4 py-2">{row.winner_party_2024 || "N/A"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function ComparePage() {
  const { data, isLoading, isError, error } = useDashboardData();
  const [stateFilter, setStateFilter] = useState("");

  const states = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.constituencies.map((c) => c.state))].sort();
  }, [data]);

  if (isLoading) return <PageLoader />;
  if (isError || !data) return <PageError message={error?.message} />;

  const seats = nationalSeatTotals(data.constituencies);
  const topSwing = data.topSwing;

  const filterRows = (rows: SwingRow[] | undefined) => {
    if (!rows) return [];
    if (!stateFilter) return rows;
    return rows.filter((r) => r.state === stateFilter);
  };

  const closest2024 = [...data.constituencies]
    .filter((c) => c.margin_2024 != null)
    .sort((a, b) => (a.margin_2024 ?? 999) - (b.margin_2024 ?? 999))
    .slice(0, 15)
    .map((c, i) => ({
      rank: i + 1,
      state: c.state,
      constituency: c.constituency,
      margin_2024: c.margin_2024,
      winner_party_2024: c.winner_party_2024,
      bjp_swing_2019_2024: c.bjp_swing_2019_2024,
      inc_swing_2019_2024: c.inc_swing_2019_2024,
    }));

  const flips = data.constituencies
    .filter((c) => c.winner_changed)
    .filter((c) => !stateFilter || c.state === stateFilter)
    .slice(0, 25)
    .map((c, i) => ({
      rank: i + 1,
      state: c.state,
      constituency: c.constituency,
      winner_party_2024: c.winner_party_2024,
      bjp_swing_2019_2024: c.bjp_swing_2019_2024,
      inc_swing_2019_2024: c.inc_swing_2019_2024,
    }));

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Compare 2019 vs 2024</h1>
        <p className="mt-1 text-sm text-muted">National and state-level election change summaries</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <MetricCard label="BJP seats 2019" value={seats.bjp_2019} />
        <MetricCard label="BJP seats 2024" value={seats.bjp_2024} accent="accent" />
        <MetricCard label="INC seats 2019" value={seats.inc_2019} />
        <MetricCard label="INC seats 2024" value={seats.inc_2024} accent="primary" />
        <MetricCard label="Seat flips" value={seats.flips} accent="warning" />
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm text-muted">Filter by state</label>
        <select
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          className="rounded-lg border border-border bg-bg px-3 py-2 text-sm"
        >
          <option value="">All India</option>
          {states.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <SwingTable title="Top seat flips (winner changed)" rows={flips as SwingRow[]} />
      <SwingTable title="Biggest BJP gains" rows={filterRows(topSwing.top_25_bjp_gains)} />
      <SwingTable title="Biggest BJP losses" rows={filterRows(topSwing.top_25_bjp_losses)} />
      <SwingTable title="Biggest INC gains" rows={filterRows(topSwing.top_25_inc_gains)} />
      <SwingTable title="Biggest INC losses" rows={filterRows(topSwing.top_25_inc_losses)} />

      <div className="rounded-xl border border-border bg-card">
        <div className="border-b border-border px-4 py-3 font-medium">Closest seats in 2024 (lowest margin)</div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-bg/50 text-left text-xs uppercase text-muted">
              <tr>
                <th className="px-4 py-2">Constituency</th>
                <th className="px-4 py-2">State</th>
                <th className="px-4 py-2">Margin 2024</th>
                <th className="px-4 py-2">Winner</th>
              </tr>
            </thead>
            <tbody>
              {closest2024
                .filter((r) => !stateFilter || r.state === stateFilter)
                .map((row) => (
                  <tr key={`${row.state}-${row.constituency}`} className="border-t border-border/60">
                    <td className="px-4 py-2">{row.constituency}</td>
                    <td className="px-4 py-2 text-muted">{row.state}</td>
                    <td className="px-4 py-2">{formatShare(row.margin_2024)}</td>
                    <td className="px-4 py-2">{row.winner_party_2024 || "N/A"}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
