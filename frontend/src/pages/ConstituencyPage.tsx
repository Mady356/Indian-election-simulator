import { Link, useParams } from "react-router-dom";
import { SeatIntelligenceCard } from "@/components/SeatIntelligenceCard";
import { ConstituencyDemographics, ConstituencyDistrictSection } from "@/components/ConstituencyDemographics";
import { ConstituencyHero } from "@/components/ConstituencyHero";
import { MetricCard } from "@/components/MetricCard";
import { MarginChart, TurnoutChart, VoteShareChart } from "@/components/SwingChart";
import { EmptyState, PageError, PageLoader } from "@/components/Layout";
import { useDashboardData } from "@/context/DataContext";
import { constituencyLookupKey } from "@/lib/data";
import { getSeatAnalysis } from "@/lib/seatAnalysis";
import {
  formatCoverageFraction,
  marginChange,
  turnoutChange,
} from "@/lib/constituencySummary";
import {
  formatShare,
  formatSwing,
  parseRouteKey,
  partyColor,
  routeStateKey,
} from "@/lib/format";
import { QUALITY_LABELS } from "@/lib/constants";
import { ArrowLeft, Compass } from "lucide-react";

function StatCell({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
      <dt className="text-[10px] font-semibold uppercase tracking-wider text-muted">{label}</dt>
      <dd className="mt-1 text-sm font-semibold tabular-nums" style={{ color: valueColor }}>
        {value}
      </dd>
    </div>
  );
}

export function ConstituencyPage() {
  const { stateKey = "", constituencyKey = "" } = useParams();
  const { data, isLoading, isError, error } = useDashboardData();

  if (isLoading) return <PageLoader />;
  if (isError || !data) return <PageError message={error?.message} />;

  const record = data.constituencyByKey.get(
    constituencyLookupKey(parseRouteKey(stateKey), parseRouteKey(constituencyKey)),
  );

  if (!record) {
    return (
      <div className="mx-auto max-w-lg space-y-4">
        <EmptyState
          title="Constituency not found"
          body="This route does not match a constituency in the current dataset."
        />
        <div className="text-center">
          <Link
            to="/"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2.5 text-sm text-primary transition hover:border-primary/50"
          >
            <Compass className="h-4 w-4" />
            Back to Explore
          </Link>
        </div>
      </div>
    );
  }

  const tChange = turnoutChange(record);
  const mChange = marginChange(record);
  const seatAnalysis = getSeatAnalysis(
    data.seatAnalysisByKey,
    record.state_key,
    record.constituency_key,
  );

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <ConstituencyHero record={record} />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <MetricCard
          label="Winner 2024"
          value={record.winner_party_2024 || "N/A"}
          accent="accent"
        />
        <MetricCard label="BJP swing" value={formatSwing(record.bjp_swing_2019_2024)} accent="accent" />
        <MetricCard label="INC swing" value={formatSwing(record.inc_swing_2019_2024)} accent="primary" />
        <MetricCard
          label="Margin change"
          value={mChange != null ? formatSwing(mChange) : "N/A"}
          hint={
            record.margin_2019 != null && record.margin_2024 != null
              ? `${formatShare(record.margin_2019)} → ${formatShare(record.margin_2024)}`
              : undefined
          }
        />
        <MetricCard
          label="Turnout change"
          value={tChange != null ? formatSwing(tChange) : "N/A"}
          hint={
            record.turnout_2019 != null && record.turnout_2024 != null
              ? `${formatShare(record.turnout_2019)} → ${formatShare(record.turnout_2024)}`
              : undefined
          }
        />
        <MetricCard
          label="Data quality"
          value={QUALITY_LABELS[record.data_quality_label] || record.data_quality_label}
        />
      </div>

      <section className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-lg font-medium">Election profile</h2>
        <p className="mt-1 text-sm text-muted">Lok Sabha results and vote movement (2019 → 2024).</p>
        <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <StatCell label="Winner 2019" value={record.winner_party_2019 || "N/A"} valueColor={partyColor(record.winner_party_2019)} />
          <StatCell label="Winner 2024" value={record.winner_party_2024 || "N/A"} valueColor={partyColor(record.winner_party_2024)} />
          <StatCell
            label="BJP vote share"
            value={`${formatShare(record.bjp_vote_share_2019)} → ${formatShare(record.bjp_vote_share_2024)}`}
            valueColor={partyColor("BJP")}
          />
          <StatCell
            label="INC vote share"
            value={`${formatShare(record.inc_vote_share_2019)} → ${formatShare(record.inc_vote_share_2024)}`}
            valueColor={partyColor("INC")}
          />
          <StatCell label="BJP swing" value={formatSwing(record.bjp_swing_2019_2024)} />
          <StatCell label="INC swing" value={formatSwing(record.inc_swing_2019_2024)} />
          <StatCell label="Margin 2019" value={formatShare(record.margin_2019)} />
          <StatCell label="Margin 2024" value={formatShare(record.margin_2024)} />
          <StatCell label="Turnout 2019" value={formatShare(record.turnout_2019)} />
          <StatCell label="Turnout 2024" value={formatShare(record.turnout_2024)} />
          <StatCell
            label="Turnout change"
            value={tChange != null ? formatSwing(tChange) : "N/A"}
          />
          <StatCell
            label="Winner changed"
            value={record.winner_changed ? "Yes" : "No"}
            valueColor={record.winner_changed ? "#FBBF24" : "#7AE582"}
          />
          <StatCell
            label="Demographic coverage"
            value={formatCoverageFraction(record.nfhs5_coverage_share)}
          />
          <StatCell
            label="Change coverage"
            value={formatCoverageFraction(record.change_coverage_share)}
          />
        </dl>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Election charts</h2>
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-border bg-card p-4">
            <VoteShareChart
              bjp2019={record.bjp_vote_share_2019}
              bjp2024={record.bjp_vote_share_2024}
              inc2019={record.inc_vote_share_2019}
              inc2024={record.inc_vote_share_2024}
            />
          </div>
          <div className="space-y-4">
            <div className="rounded-xl border border-border bg-card p-4">
              <MarginChart margin2019={record.margin_2019} margin2024={record.margin_2024} />
            </div>
            <div className="rounded-xl border border-border bg-card p-4">
              <TurnoutChart turnout2019={record.turnout_2019} turnout2024={record.turnout_2024} />
            </div>
          </div>
        </div>
      </section>

      <SeatIntelligenceCard analysis={seatAnalysis} />

      <ConstituencyDemographics record={record} />

      <ConstituencyDistrictSection record={record} />

      <div className="flex flex-wrap gap-3">
        <Link
          to={`/state/${routeStateKey(record.state_key)}`}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-white transition hover:bg-primary/90"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to state dashboard
        </Link>
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2.5 text-sm font-medium text-text transition hover:border-primary/50 hover:text-primary"
        >
          <Compass className="h-4 w-4" />
          Explore another constituency
        </Link>
      </div>

      <p className="rounded-xl border border-border bg-card/60 px-4 py-4 text-xs leading-relaxed text-muted">
        This page combines constituency election results with district-linked demographic indicators.
        Missing demographic values are not imputed. Relationships shown are descriptive, not causal.
      </p>
    </div>
  );
}
