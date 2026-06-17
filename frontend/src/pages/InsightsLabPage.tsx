import { CoverageWarning } from "@/components/CoverageWarning";
import { MetricCard } from "@/components/MetricCard";
import { PageError, PageLoader } from "@/components/Layout";
import { useDashboardData } from "@/context/DataContext";
import { featureLabel, formatNumber } from "@/lib/format";
import type { InsightRow } from "@/lib/data";

function InsightList({
  title,
  rows,
  positive,
}: {
  title: string;
  rows: InsightRow[];
  positive: boolean;
}) {
  if (!rows.length) return null;
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <h3 className="font-medium">{title}</h3>
      <div className="mt-3 space-y-3">
        {rows.map((row) => (
          <div key={row.feature} className="rounded-lg border border-border/70 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">{featureLabel(row.feature)}</span>
              <span className={positive ? "text-accent" : "text-danger"}>
                r = {row.correlation?.toFixed(3) ?? "N/A"}
              </span>
            </div>
            <p className="mt-1 text-xs text-muted">n = {formatNumber(row.n_observations)} constituencies</p>
            <p className="mt-2 text-xs text-muted">{row.interpretation}</p>
            <p className="mt-2 text-[11px] italic text-muted">
              This is a constituency-level exploratory relationship, not a causal claim.
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

export function InsightsLabPage() {
  const { data, isLoading, isError, error } = useDashboardData();

  if (isLoading) return <PageLoader />;
  if (isError || !data) return <PageError message={error?.message} />;

  const insights = data.insights;
  const lowVars = data.variableCoverage.filter((v) => (v.non_null_pct ?? 0) < 20).slice(0, 6);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Insights Lab</h1>
        <p className="mt-1 text-sm text-muted">{insights.disclaimer}</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <MetricCard
          label="Constituencies in master"
          value={data.coverageSummary.election_constituencies_total}
        />
        <MetricCard
          label="With demographics"
          value={data.coverageSummary.constituencies_with_demographic_coverage}
        />
        <MetricCard
          label="With change features"
          value={data.coverageSummary.constituencies_with_change_features}
        />
      </div>

      <CoverageWarning
        title="Exploratory analysis only"
        message="Correlations describe patterns across constituencies with available data. They do not prove causation and should not be used for forecasting without additional validation."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <InsightList title="Strongest positive BJP swing correlations" rows={insights.bjp_swing_positive} positive />
        <InsightList title="Strongest negative BJP swing correlations" rows={insights.bjp_swing_negative} positive={false} />
        <InsightList title="Strongest positive INC swing correlations" rows={insights.inc_swing_positive} positive />
        <InsightList title="Strongest negative INC swing correlations" rows={insights.inc_swing_negative} positive={false} />
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <h3 className="font-medium">Variable coverage warnings</h3>
        <p className="mt-1 text-sm text-muted">
          These indicators have limited constituency coverage; interpret correlations cautiously.
        </p>
        <ul className="mt-3 space-y-2 text-sm">
          {lowVars.map((v) => (
            <li key={v.variable} className="flex justify-between border-b border-border/50 py-2">
              <span>{featureLabel(v.variable)}</span>
              <span className="text-muted">{v.non_null_pct?.toFixed(1)}% coverage</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
