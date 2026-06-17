import { Link, useParams } from "react-router-dom";
import { CoverageWarning } from "@/components/CoverageWarning";
import { DataQualityBadge } from "@/components/DataQualityBadge";
import { MetricCard } from "@/components/MetricCard";
import { MarginChart, TurnoutChart, VoteShareChart } from "@/components/SwingChart";
import { EmptyState, PageError, PageLoader } from "@/components/Layout";
import { useDashboardData } from "@/context/DataContext";
import { constituencyLookupKey, hasDemographics } from "@/lib/data";
import { featureLabel, formatShare, formatSwing, parseRouteKey } from "@/lib/format";

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
      <EmptyState
        title="Constituency not found"
        body="This route does not match a constituency in the current dataset."
      />
    );
  }

  const demo = hasDemographics(record);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm text-muted">
            <Link to="/" className="hover:text-primary">
              Explore
            </Link>{" "}
            / {record.state}
          </p>
          <h1 className="mt-1 text-3xl font-semibold">{record.constituency}</h1>
        </div>
        <DataQualityBadge label={record.data_quality_label} />
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Winner 2019" value={record.winner_party_2019 || "N/A"} />
        <MetricCard label="Winner 2024" value={record.winner_party_2024 || "N/A"} accent="accent" />
        <MetricCard label="BJP swing" value={formatSwing(record.bjp_swing_2019_2024)} />
        <MetricCard label="INC swing" value={formatSwing(record.inc_swing_2019_2024)} />
      </div>

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

      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-lg font-medium">Demographic profile</h2>
        {!demo ? (
          <div className="mt-3">
            <CoverageWarning message="Election data is available for this constituency, but demographic coverage is not yet available." />
          </div>
        ) : (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(record.demographics_nfhs5)
              .filter(([, v]) => v != null)
              .map(([k, v]) => (
                <div key={k} className="rounded-lg border border-border p-3">
                  <div className="text-xs text-muted">{featureLabel(k)}</div>
                  <div className="mt-1 text-lg font-semibold tabular-nums">
                    {typeof v === "number" ? v.toFixed(1) : "N/A"}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-lg font-medium">Coverage</h2>
        <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted">NFHS-5 coverage share</dt>
            <dd className="font-medium">{formatShare((record.nfhs5_coverage_share ?? 0) * 100)}</dd>
          </div>
          <div>
            <dt className="text-muted">Change feature coverage</dt>
            <dd className="font-medium">{formatShare((record.change_coverage_share ?? 0) * 100)}</dd>
          </div>
          <div>
            <dt className="text-muted">Districts used</dt>
            <dd>{record.districts_used || "N/A"}</dd>
          </div>
          <div>
            <dt className="text-muted">Districts missing</dt>
            <dd className={record.districts_missing ? "text-warning" : ""}>
              {record.districts_missing || "None listed"}
            </dd>
          </div>
        </dl>
        <p className="mt-4 text-xs text-muted">
          Values are mapped from district-level NFHS indicators where constituency crosswalk coverage
          exists. Missing values are not imputed.
        </p>
      </div>
    </div>
  );
}
