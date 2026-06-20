import { Link } from "react-router-dom";
import { DataQualityBadge } from "./DataQualityBadge";
import type { ProjectedConstituency, ProjectionConfidence } from "@/lib/simulator";
import { formatConfidenceLabel } from "@/lib/simulator";
import { formatShare, routeConstituencyKey, routeStateKey } from "@/lib/format";

function confidenceClass(confidence: ProjectionConfidence): string {
  switch (confidence) {
    case "high":
      return "text-accent border-accent/30 bg-accent/10";
    case "medium":
      return "text-primary border-primary/30 bg-primary/10";
    default:
      return "text-warning border-warning/30 bg-warning/10";
  }
}

interface ScenarioResultsTableProps {
  rows: ProjectedConstituency[];
  showOnlyChanged: boolean;
  showOnlyClose: boolean;
  confidenceFilter: "" | ProjectionConfidence;
  stateFilter: string | null;
}

export function ScenarioResultsTable({
  rows,
  showOnlyChanged,
  showOnlyClose,
  confidenceFilter,
  stateFilter,
}: ScenarioResultsTableProps) {
  let filtered = rows;
  if (showOnlyChanged) filtered = filtered.filter((row) => row.winner_changed);
  if (showOnlyClose) filtered = filtered.filter((row) => (row.projected_margin ?? 999) <= 5);
  if (confidenceFilter) filtered = filtered.filter((row) => row.projection_confidence === confidenceFilter);
  if (stateFilter) filtered = filtered.filter((row) => row.state === stateFilter);

  const sorted = [...filtered].sort((a, b) => {
    if (a.winner_changed !== b.winner_changed) return a.winner_changed ? -1 : 1;
    return (a.projected_margin ?? 999) - (b.projected_margin ?? 999);
  });

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-medium">Scenario impact table</h2>
        <p className="mt-0.5 text-xs text-muted">
          {sorted.length} constituencies shown · click a row to open the full profile
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-bg/60 text-left text-xs uppercase tracking-wide text-muted">
            <tr>
              <th className="px-4 py-2.5">Constituency</th>
              <th className="px-4 py-2.5">State</th>
              <th className="px-4 py-2.5">2024 winner</th>
              <th className="px-4 py-2.5">Projected winner</th>
              <th className="px-4 py-2.5">Proj. BJP</th>
              <th className="px-4 py-2.5">Proj. INC</th>
              <th className="px-4 py-2.5">Proj. margin</th>
              <th className="px-4 py-2.5">Changed</th>
              <th className="px-4 py-2.5">Confidence</th>
              <th className="px-4 py-2.5">Data quality</th>
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 ? (
              <tr>
                <td colSpan={10} className="px-4 py-8 text-center text-muted">
                  No constituencies match the current scenario filters.
                </td>
              </tr>
            ) : (
              sorted.slice(0, 150).map((row) => (
                <tr
                  key={`${row.state_key}-${row.constituency_key}`}
                  className="border-t border-border/70 hover:bg-primary/5"
                >
                  <td className="px-4 py-2.5">
                    <Link
                      to={`/constituency/${routeStateKey(row.state_key)}/${routeConstituencyKey(row.constituency_key)}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {row.constituency}
                    </Link>
                    {row.limited_projection_note ? (
                      <p className="mt-1 max-w-xs text-[10px] leading-snug text-warning">
                        {row.limited_projection_note}
                      </p>
                    ) : null}
                  </td>
                  <td className="px-4 py-2.5 text-muted">{row.state}</td>
                  <td className="px-4 py-2.5">{row.winner_party_2024 || "N/A"}</td>
                  <td className="px-4 py-2.5 font-medium">{row.projected_winner}</td>
                  <td className="px-4 py-2.5 tabular-nums">
                    {row.projected_bjp_share != null ? formatShare(row.projected_bjp_share) : "N/A"}
                  </td>
                  <td className="px-4 py-2.5 tabular-nums">
                    {row.projected_inc_share != null ? formatShare(row.projected_inc_share) : "N/A"}
                  </td>
                  <td className="px-4 py-2.5 tabular-nums">
                    {row.projected_margin != null ? formatShare(row.projected_margin) : "N/A"}
                  </td>
                  <td className="px-4 py-2.5">{row.winner_changed ? "Yes" : "No"}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-medium ${confidenceClass(row.projection_confidence)}`}
                    >
                      {formatConfidenceLabel(row.projection_confidence)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <DataQualityBadge label={row.data_quality_label} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
