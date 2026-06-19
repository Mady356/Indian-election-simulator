import { Link, useParams } from "react-router-dom";
import { Info } from "lucide-react";
import { CoverageWarning } from "@/components/CoverageWarning";
import { DataQualityBadge } from "@/components/DataQualityBadge";
import { MetricCard } from "@/components/MetricCard";
import { StateConstituencyTable } from "@/components/StateConstituencyTable";
import { StateMovementsSection } from "@/components/StateMovementsSection";
import { EmptyState, PageError, PageLoader } from "@/components/Layout";
import { useDashboardData } from "@/context/DataContext";
import { computeStateMovements } from "@/lib/stateMovements";
import { formatNumber, formatShare, formatSwing, parseRouteKey } from "@/lib/format";
import { normalizeKey } from "@/lib/format";

function seatChange(current: number, previous: number): string {
  const delta = current - previous;
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta}`;
}

export function StatePage() {
  const { stateKey = "" } = useParams();
  const { data, isLoading, isError, error } = useDashboardData();

  if (isLoading) return <PageLoader />;
  if (isError || !data) return <PageError message={error?.message} />;

  const state = data.stateByKey.get(normalizeKey(parseRouteKey(stateKey)));
  if (!state) {
    return <EmptyState title="State not found" body="This state is not in the current dataset." />;
  }

  const constituencies = data.constituencies
    .filter((c) => normalizeKey(c.state_key) === normalizeKey(state.state_key))
    .sort((a, b) => a.constituency.localeCompare(b.constituency));

  if (constituencies.length === 0) {
    return (
      <EmptyState
        title="No constituencies found"
        body={`Election data for ${state.state} is not available in the current bundle.`}
      />
    );
  }

  const movements = computeStateMovements(constituencies);
  const hasAnyDemographics = state.constituencies_with_demographics > 0;
  const noDemographics = state.constituencies_with_demographics === 0;
  const partialDemographics =
    hasAnyDemographics && state.constituencies_with_demographics < state.total_constituencies;

  const bjpSeatDelta = state.bjp_seats_2024 - state.bjp_seats_2019;
  const incSeatDelta = state.inc_seats_2024 - state.inc_seats_2019;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="rounded-xl border border-border bg-gradient-to-br from-card via-card to-primary/5 p-5 md:p-6">
        <p className="text-sm text-muted">
          <Link to="/" className="hover:text-primary">
            Explore
          </Link>{" "}
          / State intelligence
        </p>

        <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">{state.state}</h1>
            <p className="mt-2 text-sm text-muted">
              State-level Lok Sabha election intelligence · {formatNumber(state.total_constituencies)}{" "}
              constituencies
            </p>
          </div>
          <DataQualityBadge label={state.data_quality_label} />
        </div>

        <dl className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              Constituencies
            </dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums">
              {formatNumber(state.total_constituencies)}
            </dd>
          </div>
          <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              With demographics
            </dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums">
              {formatNumber(state.constituencies_with_demographics)}
              <span className="ml-1 text-sm font-normal text-muted">
                ({formatShare(state.demographic_coverage_pct)})
              </span>
            </dd>
          </div>
          <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              BJP seats
            </dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums">
              {state.bjp_seats_2019} → {state.bjp_seats_2024}
            </dd>
          </div>
          <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              INC seats
            </dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums">
              {state.inc_seats_2019} → {state.inc_seats_2024}
            </dd>
          </div>
          <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              Seat flips
            </dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums">{state.winner_changes}</dd>
          </div>
          <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              Avg BJP swing
            </dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums">
              {formatSwing(state.average_bjp_swing)}
            </dd>
          </div>
          <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              Avg INC swing
            </dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums">
              {formatSwing(state.average_inc_swing)}
            </dd>
          </div>
          <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              Avg turnout change
            </dt>
            <dd className="mt-1 text-lg font-semibold tabular-nums">
              {formatSwing(state.average_turnout_change)}
            </dd>
          </div>
        </dl>
      </div>

      {noDemographics ? (
        <CoverageWarning
          title="Demographic data unavailable"
          message="Demographic indicators are not available for any constituency in this state. Election results and swing analysis below remain available."
        />
      ) : partialDemographics ? (
        <CoverageWarning
          message={`Only ${state.constituencies_with_demographics} of ${state.total_constituencies} constituencies have demographic coverage in this state.`}
        />
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <MetricCard
          label="BJP seat change"
          value={seatChange(state.bjp_seats_2024, state.bjp_seats_2019)}
          hint={`${state.bjp_seats_2019} → ${state.bjp_seats_2024} seats`}
          accent={bjpSeatDelta >= 0 ? "accent" : "danger"}
        />
        <MetricCard
          label="INC seat change"
          value={seatChange(state.inc_seats_2024, state.inc_seats_2019)}
          hint={`${state.inc_seats_2019} → ${state.inc_seats_2024} seats`}
          accent={incSeatDelta >= 0 ? "primary" : "danger"}
        />
        <MetricCard
          label="Flipped seats"
          value={state.winner_changes}
          hint="Winner changed 2019 → 2024"
          accent="warning"
        />
        <MetricCard
          label="Demographic coverage"
          value={formatShare(state.demographic_coverage_pct)}
          hint={`${state.constituencies_with_demographics} of ${state.total_constituencies} constituencies`}
        />
        <MetricCard label="Average BJP swing" value={formatSwing(state.average_bjp_swing)} accent="accent" />
        <MetricCard label="Average INC swing" value={formatSwing(state.average_inc_swing)} accent="primary" />
      </div>

      <div className="flex gap-3 rounded-xl border border-border bg-card/60 p-4 text-sm">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
        <p className="text-muted">
          Demographic coverage varies across constituencies. Missing values are not imputed.
          State-level averages are calculated only from available constituency data.
        </p>
      </div>

      <StateMovementsSection movements={movements} stateKey={state.state_key} />

      <StateConstituencyTable constituencies={constituencies} stateKey={state.state_key} />
    </div>
  );
}
