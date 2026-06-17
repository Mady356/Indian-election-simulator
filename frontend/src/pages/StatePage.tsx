import { Link, useParams } from "react-router-dom";
import { CoverageWarning } from "@/components/CoverageWarning";
import { DataQualityBadge } from "@/components/DataQualityBadge";
import { MetricCard } from "@/components/MetricCard";
import { EmptyState, PageError, PageLoader } from "@/components/Layout";
import { useDashboardData } from "@/context/DataContext";
import { formatShare, formatSwing, parseRouteKey, routeConstituencyKey, routeStateKey } from "@/lib/format";
import { normalizeKey } from "@/lib/format";

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

  const lowCoverage = state.data_quality_label === "election_only" || state.data_quality_label === "low";

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm text-muted">
            <Link to="/" className="hover:text-primary">
              Explore
            </Link>{" "}
            / State
          </p>
          <h1 className="mt-1 text-3xl font-semibold">{state.state}</h1>
        </div>
        <DataQualityBadge label={state.data_quality_label} />
      </div>

      {lowCoverage ? (
        <CoverageWarning
          message={`Only ${state.constituencies_with_demographics} of ${state.total_constituencies} constituencies have demographic coverage in this state.`}
        />
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Total seats" value={state.total_constituencies} />
        <MetricCard label="Demo coverage" value={formatShare(state.demographic_coverage_pct)} />
        <MetricCard
          label="BJP seats"
          value={`${state.bjp_seats_2019} → ${state.bjp_seats_2024}`}
          hint={`${state.bjp_seats_2024 - state.bjp_seats_2019 >= 0 ? "+" : ""}${state.bjp_seats_2024 - state.bjp_seats_2019}`}
        />
        <MetricCard
          label="INC seats"
          value={`${state.inc_seats_2019} → ${state.inc_seats_2024}`}
          hint={`${state.inc_seats_2024 - state.inc_seats_2019 >= 0 ? "+" : ""}${state.inc_seats_2024 - state.inc_seats_2019}`}
        />
        <MetricCard label="Seat changes" value={state.winner_changes} />
        <MetricCard label="Avg BJP swing" value={formatSwing(state.average_bjp_swing)} />
        <MetricCard label="Avg INC swing" value={formatSwing(state.average_inc_swing)} />
        <MetricCard label="Avg turnout Δ" value={formatSwing(state.average_turnout_change)} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-border bg-card p-4">
          <h3 className="font-medium">Top BJP gain</h3>
          {state.top_bjp_gain ? (
            <p className="mt-2 text-sm">
              <Link
                className="text-primary hover:underline"
                to={`/constituency/${routeStateKey(state.state_key)}/${routeConstituencyKey(state.top_bjp_gain.constituency_key)}`}
              >
                {state.top_bjp_gain.constituency}
              </Link>{" "}
              · {formatSwing(state.top_bjp_gain.swing)}
            </p>
          ) : (
            <p className="mt-2 text-sm text-muted">N/A</p>
          )}
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <h3 className="font-medium">Top INC gain</h3>
          {state.top_inc_gain ? (
            <p className="mt-2 text-sm">
              <Link
                className="text-primary hover:underline"
                to={`/constituency/${routeStateKey(state.state_key)}/${routeConstituencyKey(state.top_inc_gain.constituency_key)}`}
              >
                {state.top_inc_gain.constituency}
              </Link>{" "}
              · {formatSwing(state.top_inc_gain.swing)}
            </p>
          ) : (
            <p className="mt-2 text-sm text-muted">N/A</p>
          )}
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <div className="border-b border-border px-4 py-3 font-medium">Constituencies</div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-bg/60 text-left text-xs uppercase text-muted">
              <tr>
                <th className="px-4 py-2">Constituency</th>
                <th className="px-4 py-2">2024 winner</th>
                <th className="px-4 py-2">BJP swing</th>
                <th className="px-4 py-2">INC swing</th>
                <th className="px-4 py-2">Coverage</th>
              </tr>
            </thead>
            <tbody>
              {constituencies.map((c) => (
                <tr key={c.constituency_key} className="border-t border-border/70 hover:bg-border/20">
                  <td className="px-4 py-2">
                    <Link
                      to={`/constituency/${routeStateKey(c.state_key)}/${routeConstituencyKey(c.constituency_key)}`}
                      className="text-primary hover:underline"
                    >
                      {c.constituency}
                    </Link>
                  </td>
                  <td className="px-4 py-2">{c.winner_party_2024 || "N/A"}</td>
                  <td className="px-4 py-2">{formatSwing(c.bjp_swing_2019_2024)}</td>
                  <td className="px-4 py-2">{formatSwing(c.inc_swing_2019_2024)}</td>
                  <td className="px-4 py-2">
                    <DataQualityBadge label={c.data_quality_label} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
