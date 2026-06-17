import { Link } from "react-router-dom";
import { DataQualityBadge } from "./DataQualityBadge";
import { MetricCard } from "./MetricCard";
import type { StateSummary } from "@/lib/data";
import { formatShare, formatSwing, routeStateKey } from "@/lib/format";

export function StateSummaryCard({ state }: { state: StateSummary }) {
  return (
    <Link
      to={`/state/${routeStateKey(state.state_key)}`}
      className="block rounded-xl border border-border bg-card p-4 transition hover:border-primary/40"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold">{state.state}</h3>
        <DataQualityBadge label={state.data_quality_label} />
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <MetricCard label="Seats" value={state.total_constituencies} />
        <MetricCard
          label="Demo coverage"
          value={formatShare(state.demographic_coverage_pct)}
          hint={`${state.constituencies_with_demographics} with demographics`}
        />
        <MetricCard
          label="BJP seats"
          value={`${state.bjp_seats_2019} → ${state.bjp_seats_2024}`}
        />
        <MetricCard
          label="INC seats"
          value={`${state.inc_seats_2019} → ${state.inc_seats_2024}`}
        />
      </div>
      <div className="mt-2 text-xs text-muted">
        Avg BJP swing {formatSwing(state.average_bjp_swing)} · {state.winner_changes} seat changes
      </div>
    </Link>
  );
}
