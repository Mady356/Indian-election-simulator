import { CoverageWarning } from "./CoverageWarning";
import type { ConstituencyRecord } from "@/lib/data";
import { hasDemographics } from "@/lib/data";
import { featureLabel } from "@/lib/format";
import { formatCoverageFraction } from "@/lib/constituencySummary";

const NFHS5_INDICATORS = [
  { key: "urban_pct", label: "Urban %" },
  { key: "electricity_pct", label: "Electricity %" },
  { key: "improved_sanitation_pct", label: "Improved sanitation %" },
  { key: "lpg_pct", label: "LPG %" },
  { key: "mobile_phone_pct", label: "Mobile phone %" },
  { key: "bank_account_pct", label: "Bank account %" },
  { key: "women_secondary_edu_pct", label: "Women secondary education %" },
  { key: "fertility_rate", label: "Fertility rate" },
  { key: "wealth_index_mean", label: "Wealth index (mean)" },
] as const;

const CHANGE_INDICATORS = [
  { key: "electricity_pct_change", label: "Electricity % change" },
  { key: "improved_sanitation_pct_change", label: "Improved sanitation % change" },
  { key: "lpg_pct_change", label: "LPG % change" },
  { key: "mobile_phone_pct_change", label: "Mobile phone % change" },
  { key: "bank_account_pct_change", label: "Bank account % change" },
  { key: "urban_pct_change", label: "Urban % change" },
  { key: "fertility_rate_change", label: "Fertility rate change" },
] as const;

function IndicatorGrid({
  title,
  description,
  items,
}: {
  title: string;
  description?: string;
  items: Array<{ label: string; value: string }>;
}) {
  if (items.length === 0) return null;

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h2 className="text-lg font-medium">{title}</h2>
      {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map(({ label, value }) => (
          <div key={label} className="rounded-lg border border-border/80 bg-bg/30 p-3">
            <div className="text-xs text-muted">{label}</div>
            <div className="mt-1 text-lg font-semibold tabular-nums">{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatIndicatorValue(key: string, value: number): string {
  if (key.includes("fertility") || key.includes("wealth_index")) {
    return value.toFixed(2);
  }
  return value.toFixed(1);
}

export function ConstituencyDemographics({ record }: { record: ConstituencyRecord }) {
  const demo = hasDemographics(record);

  const nfhs5Items = NFHS5_INDICATORS.flatMap(({ key, label }) => {
    const value = record.demographics_nfhs5[key as keyof typeof record.demographics_nfhs5];
    if (value == null || Number.isNaN(value)) return [];
    return [{ label: `${featureLabel(key)} (NFHS-5)`, value: formatIndicatorValue(key, value) }];
  });

  const changeItems = CHANGE_INDICATORS.flatMap(({ key, label }) => {
    const value = record.demographics_change[key as keyof typeof record.demographics_change];
    if (value == null || Number.isNaN(value)) return [];
    const sign = value > 0 ? "+" : "";
    return [{ label, value: `${sign}${value.toFixed(2)}` }];
  });

  return (
    <>
      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-lg font-medium">Demographic profile</h2>
        <p className="mt-1 text-sm text-muted">
          District-linked NFHS-5 indicators where coverage permits.
        </p>
        {!demo || nfhs5Items.length === 0 ? (
          <div className="mt-4">
            <CoverageWarning message="Election data is available for this constituency, but demographic coverage is not yet available." />
          </div>
        ) : (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {nfhs5Items.map(({ label, value }) => (
              <div key={label} className="rounded-lg border border-border/80 bg-bg/30 p-3">
                <div className="text-xs text-muted">{label}</div>
                <div className="mt-1 text-lg font-semibold tabular-nums">{value}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {changeItems.length > 0 ? (
        <IndicatorGrid
          title="Demographic change"
          description="Change indicators are based on available district-linked NFHS data and may have partial coverage."
          items={changeItems}
        />
      ) : null}
    </>
  );
}

export function ConstituencyDistrictSection({ record }: { record: ConstituencyRecord }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h2 className="text-lg font-medium">District composition</h2>
      <p className="mt-1 text-sm text-muted">
        How constituency-level demographics are mapped from districts.
      </p>

      {record.districts_missing ? (
        <div className="mt-4">
          <CoverageWarning
            title="Incomplete district mapping"
            message={`Some districts could not be mapped: ${record.districts_missing}`}
          />
        </div>
      ) : null}

      <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
        <div className="rounded-lg border border-border/80 bg-bg/30 p-3">
          <dt className="text-xs text-muted">Districts used</dt>
          <dd className="mt-1 font-medium">{record.districts_used || "N/A"}</dd>
        </div>
        <div className="rounded-lg border border-border/80 bg-bg/30 p-3">
          <dt className="text-xs text-muted">Districts missing</dt>
          <dd className={`mt-1 font-medium ${record.districts_missing ? "text-warning" : ""}`}>
            {record.districts_missing || "None listed"}
          </dd>
        </div>
        <div className="rounded-lg border border-border/80 bg-bg/30 p-3">
          <dt className="text-xs text-muted">NFHS-5 coverage share</dt>
          <dd className="mt-1 font-medium tabular-nums">
            {formatCoverageFraction(record.nfhs5_coverage_share)}
          </dd>
        </div>
        <div className="rounded-lg border border-border/80 bg-bg/30 p-3">
          <dt className="text-xs text-muted">Change coverage share</dt>
          <dd className="mt-1 font-medium tabular-nums">
            {formatCoverageFraction(record.change_coverage_share)}
          </dd>
        </div>
        {record.change_quality_flag ? (
          <div className="rounded-lg border border-border/80 bg-bg/30 p-3 sm:col-span-2">
            <dt className="text-xs text-muted">Change quality flag</dt>
            <dd className="mt-1 font-medium">{record.change_quality_flag}</dd>
          </div>
        ) : null}
      </dl>
    </div>
  );
}
