import { Link } from "react-router-dom";
import type { SeatSimulationStats } from "@/lib/monteCarlo";
import { formatProbability } from "@/lib/monteCarlo";
import { routeConstituencyKey, routeStateKey } from "@/lib/format";

function confidenceClass(confidence: string): string {
  switch (confidence) {
    case "high":
      return "text-accent border-accent/30 bg-accent/10";
    case "medium":
      return "text-primary border-primary/30 bg-primary/10";
    default:
      return "text-warning border-warning/30 bg-warning/10";
  }
}

export function VolatileSeatsTable({ rows }: { rows: SeatSimulationStats[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-medium">Most volatile seats</h2>
        <p className="mt-0.5 text-xs text-muted">
          Constituencies that change alliance winner most often across simulations
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-bg/60 text-left text-xs uppercase tracking-wide text-muted">
            <tr>
              <th className="px-4 py-2.5">Constituency</th>
              <th className="px-4 py-2.5">State</th>
              <th className="px-4 py-2.5">2024 winner</th>
              <th className="px-4 py-2.5">Most common sim. winner</th>
              <th className="px-4 py-2.5">Winner-change prob.</th>
              <th className="px-4 py-2.5">NDA/BJP</th>
              <th className="px-4 py-2.5">INDIA/INC</th>
              <th className="px-4 py-2.5">Others</th>
              <th className="px-4 py-2.5">Projection confidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-muted">
                  Run simulations to identify volatile seats.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={`${row.state_key}-${row.constituency_key}`} className="border-t border-border/70">
                  <td className="px-4 py-2.5">
                    <Link
                      to={`/constituency/${routeStateKey(row.state_key)}/${routeConstituencyKey(row.constituency_key)}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {row.constituency}
                    </Link>
                    {row.projection_confidence === "low" ? (
                      <p className="mt-1 max-w-xs text-[10px] text-warning">
                        Limited-confidence projection: regional-party vote shares may be incomplete.
                      </p>
                    ) : null}
                  </td>
                  <td className="px-4 py-2.5 text-muted">{row.state}</td>
                  <td className="px-4 py-2.5">{row.winner_party_2024 || "N/A"}</td>
                  <td className="px-4 py-2.5">{row.most_common_simulated_winner}</td>
                  <td className="px-4 py-2.5 tabular-nums">{formatProbability(row.flip_probability)}</td>
                  <td className="px-4 py-2.5 tabular-nums">{formatProbability(row.nda_win_probability)}</td>
                  <td className="px-4 py-2.5 tabular-nums">{formatProbability(row.india_win_probability)}</td>
                  <td className="px-4 py-2.5 tabular-nums">{formatProbability(row.others_win_probability)}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-medium capitalize ${confidenceClass(row.projection_confidence)}`}
                    >
                      {row.projection_confidence}
                    </span>
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
