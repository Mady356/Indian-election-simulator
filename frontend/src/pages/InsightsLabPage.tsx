import { Link } from "react-router-dom";
import { ArrowRight, BookOpen } from "lucide-react";
import { CoverageWarning } from "@/components/CoverageWarning";
import { MetricCard } from "@/components/MetricCard";
import { PageError, PageLoader } from "@/components/Layout";
import { getEssayBySlug } from "@/content/essays";
import { useDashboardData } from "@/context/DataContext";
import { featureLabel, formatNumber } from "@/lib/format";
import type { InsightRow } from "@/lib/data";

const FEATURED_ESSAY_SLUG = "india-urban-bjp-exception";

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
  const featuredEssay = getEssayBySlug(FEATURED_ESSAY_SLUG);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Insights Lab</h1>
        <p className="mt-1 text-sm text-muted">{insights.disclaimer}</p>
      </div>

      {featuredEssay ? (
        <section className="rounded-xl border border-primary/30 bg-gradient-to-br from-card via-card to-primary/5 p-5 md:p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div className="max-w-3xl">
              <div className="flex items-center gap-2 text-primary">
                <BookOpen className="h-4 w-4" />
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em]">
                  {featuredEssay.series}
                </span>
              </div>
              <h2 className="mt-2 text-lg font-semibold text-text">{featuredEssay.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted">{featuredEssay.dek}</p>
            </div>
            <Link
              to={`/essays/${featuredEssay.slug}`}
              className="inline-flex shrink-0 items-center gap-2 self-start rounded-lg border border-primary/30 bg-primary/10 px-4 py-2.5 text-sm font-medium text-primary transition hover:bg-primary/15"
            >
              Read essay
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>
      ) : null}

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
