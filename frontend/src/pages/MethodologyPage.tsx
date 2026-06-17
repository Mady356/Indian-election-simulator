import { DataQualityBadge } from "@/components/DataQualityBadge";
import { MetricCard } from "@/components/MetricCard";
import { PageError, PageLoader } from "@/components/Layout";
import { useDashboardData } from "@/context/DataContext";
import { APP_DISCLAIMER } from "@/lib/constants";
import { formatShare } from "@/lib/format";

export function MethodologyPage() {
  const { data, isLoading, isError, error } = useDashboardData();

  if (isLoading) return <PageLoader />;
  if (isError || !data) return <PageError message={error?.message} />;

  const cov = data.coverageSummary;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Methodology & data coverage</h1>
        <p className="mt-1 text-sm text-muted">
          Transparent documentation of what this dashboard includes — and what is still pending.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <MetricCard
          label="Election results coverage"
          value={`${cov.election_constituencies_total} / ${cov.election_constituencies_total}`}
          hint="2019 & 2024 Lok Sabha comparison spine"
          accent="accent"
        />
        <MetricCard
          label="Demographic coverage"
          value={`${cov.constituencies_with_demographic_coverage} / ${cov.election_constituencies_total}`}
          hint={formatShare(cov.demographic_coverage_pct)}
        />
      </div>

      <section className="space-y-3 rounded-xl border border-border bg-card p-5 text-sm leading-relaxed text-muted">
        <h2 className="text-lg font-medium text-text">Data sources</h2>
        <ul className="list-disc space-y-2 pl-5">
          {cov.sources.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ul>
      </section>

      <section className="space-y-3 rounded-xl border border-border bg-card p-5 text-sm leading-relaxed text-muted">
        <h2 className="text-lg font-medium text-text">CSDS / Lokniti layer</h2>
        <p>
          Status: <strong className="text-warning">{cov.csds_status}</strong>. Opinion-poll and
          vote-bank modules are under active taxonomy-guided extraction and human review. They are
          not yet shown in this public MVP.
        </p>
      </section>

      <section className="space-y-3 rounded-xl border border-border bg-card p-5 text-sm leading-relaxed text-muted">
        <h2 className="text-lg font-medium text-text">Why some constituencies are election-only</h2>
        <p>
          Demographic indicators are mapped from NFHS district features through delimitation
          crosswalks. When a constituency lacks a reliable district mapping or falls below coverage
          thresholds, we show election results only rather than imputing missing values.
        </p>
        <ul className="list-disc space-y-1 pl-5">
          {Object.entries(cov.missing_reason_counts).map(([reason, count]) => (
            <li key={reason}>
              {reason.replace(/_/g, " ")}: {count} constituencies
            </li>
          ))}
        </ul>
      </section>

      <section className="space-y-3 rounded-xl border border-border bg-card p-5 text-sm leading-relaxed text-muted">
        <h2 className="text-lg font-medium text-text">Coverage share & quality labels</h2>
        <p>
          <code className="text-text">nfhs5_coverage_share</code> estimates how much of a
          constituency&apos;s mapped district population is represented in NFHS-5 features. Quality
          labels:
        </p>
        <div className="flex flex-wrap gap-2 pt-2">
          <DataQualityBadge label="high" />
          <DataQualityBadge label="medium" />
          <DataQualityBadge label="low" />
          <DataQualityBadge label="election_only" />
        </div>
        <ul className="mt-3 list-disc space-y-1 pl-5">
          {cov.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border border-primary/20 bg-primary/5 p-5 text-sm leading-relaxed text-muted">
        <h2 className="text-lg font-medium text-text">About The 543</h2>
        <p className="mt-2">{APP_DISCLAIMER}</p>
        <p className="mt-3">
          Published at{" "}
          <a href="https://the543.org" className="text-primary hover:underline">
            the543.org
          </a>
          . The 543 refers to Lok Sabha constituencies; this release covers{" "}
          {cov.election_constituencies_total} seats with 2019 and 2024 results.
        </p>
      </section>

      <section className="rounded-xl border border-border bg-card p-5 text-sm text-muted">
        <h2 className="text-lg font-medium text-text">Analysis principles</h2>
        <ul className="mt-3 list-disc space-y-2 pl-5">
          <li>Missing demographic values are not imputed.</li>
          <li>Insights Lab correlations are exploratory, not causal.</li>
          <li>State and constituency summaries use the same static JSON bundle as the map.</li>
          <li>Rebuild data with <code className="text-text">python -m src.export.build_frontend_data_bundle</code>.</li>
        </ul>
      </section>
    </div>
  );
}
