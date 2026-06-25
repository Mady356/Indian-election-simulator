import { CoverageWarning } from "./CoverageWarning";
import type { ConstituencyRecord, DemographicFieldSource } from "@/lib/data";
import { hasDemographics } from "@/lib/data";
import { DEMOGRAPHIC_SOURCE_LABELS } from "@/lib/constants";
import { featureLabel } from "@/lib/format";
import { formatCoverageFraction } from "@/lib/constituencySummary";
import { Info } from "lucide-react";

const NFHS5_INDICATORS = [
  { key: "urban_pct", label: "Urban %" },
  { key: "electricity_pct", label: "Electricity %" },
  { key: "improved_sanitation_pct", label: "Improved sanitation %" },
  { key: "lpg_pct", label: "LPG %" },
  { key: "mobile_phone_pct", label: "Mobile phone %" },
  { key: "bank_account_pct", label: "Bank account %" },
  { key: "women_secondary_edu_pct", label: "Women secondary education %" },
  { key: "female_literacy_pct", label: "Female literacy %" },
  { key: "male_literacy_pct", label: "Male literacy %" },
  { key: "fertility_rate", label: "Fertility rate" },
  { key: "wealth_index_mean", label: "Wealth index (mean)" },
] as const;

const MANUAL_ONLY_INDICATORS = [
  { key: "literacy_rate", label: "Literacy rate" },
  { key: "sc_pct", label: "SC %" },
  { key: "st_pct", label: "ST %" },
  { key: "religion_hindu_pct", label: "Hindu %" },
  { key: "religion_muslim_pct", label: "Muslim %" },
  { key: "religion_christian_pct", label: "Christian %" },
  { key: "religion_sikh_pct", label: "Sikh %" },
  { key: "population_density", label: "Population density" },
  { key: "sex_ratio", label: "Sex ratio" },
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

function DemographicSourceBadge({ sourceType }: { sourceType?: string }) {
  if (!sourceType || sourceType === "generated" || sourceType === "election_only") {
    return null;
  }

  const label = DEMOGRAPHIC_SOURCE_LABELS[sourceType] || sourceType;
  const tone =
    sourceType === "manual"
      ? "border-warning/40 bg-warning/10 text-warning"
      : "border-primary/40 bg-primary/10 text-primary";

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${tone}`}>
      {label}
    </span>
  );
}

function SourceDetails({ source }: { source: DemographicFieldSource }) {
  return (
    <div className="mt-2 space-y-1 rounded-md border border-border/60 bg-bg/40 p-2 text-[11px] leading-relaxed text-muted">
      <div>
        <span className="font-medium text-text">Source:</span> {source.source_name}
        {source.source_year ? `, ${source.source_year}` : ""}
      </div>
      {source.method ? (
        <div>
          <span className="font-medium text-text">Method:</span> {source.method}
        </div>
      ) : null}
      {source.confidence ? (
        <div>
          <span className="font-medium text-text">Confidence:</span> {source.confidence}
        </div>
      ) : null}
      {source.value_origin === "manual_reference" && source.manual_reference_value != null ? (
        <div>
          <span className="font-medium text-text">Manual reference:</span>{" "}
          {source.manual_reference_value}
          <span className="ml-1 text-warning">(generated value shown above)</span>
        </div>
      ) : null}
    </div>
  );
}

function IndicatorCard({
  label,
  value,
  source,
  manualTag,
}: {
  label: string;
  value: string;
  source?: DemographicFieldSource;
  manualTag?: string;
}) {
  return (
    <div className="rounded-lg border border-border/80 bg-bg/30 p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="text-xs text-muted">{label}</div>
        {manualTag ? (
          <span className="shrink-0 rounded bg-warning/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-warning">
            {manualTag}
          </span>
        ) : null}
      </div>
      <div className="mt-1 text-lg font-semibold tabular-nums">{value}</div>
      {source ? <SourceDetails source={source} /> : null}
    </div>
  );
}

function IndicatorGrid({
  title,
  description,
  items,
}: {
  title: string;
  description?: string;
  items: Array<{ label: string; value: string; source?: DemographicFieldSource; manualTag?: string }>;
}) {
  if (items.length === 0) return null;

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h2 className="text-lg font-medium">{title}</h2>
      {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map(({ label, value, source, manualTag }) => (
          <IndicatorCard key={label} label={label} value={value} source={source} manualTag={manualTag} />
        ))}
      </div>
    </div>
  );
}

function formatIndicatorValue(key: string, value: number): string {
  if (key.includes("fertility") || key.includes("wealth_index")) {
    return value.toFixed(2);
  }
  if (key === "population_density" || key === "sex_ratio") {
    return value.toFixed(0);
  }
  return value.toFixed(1);
}

function manualTagForSource(source?: DemographicFieldSource): string | undefined {
  if (!source) return undefined;
  if (source.value_origin === "manual" || source.value_origin === "manual_override") {
    return "Manual";
  }
  if (source.value_origin === "manual_reference") {
    return "Ref";
  }
  return undefined;
}

export function ConstituencyDemographics({ record }: { record: ConstituencyRecord }) {
  const demo = hasDemographics(record);
  const fieldSources = record.demographic_field_sources || {};
  const sourceType = record.demographic_source_type;
  const hasManualLayer = sourceType === "manual" || sourceType === "mixed";

  const nfhs5Items = NFHS5_INDICATORS.flatMap(({ key, label }) => {
    const value = record.demographics_nfhs5[key as keyof typeof record.demographics_nfhs5];
    if (value == null || Number.isNaN(value)) return [];
    const source = fieldSources[key];
    const suffix = source?.value_origin?.startsWith("manual") ? "" : " (NFHS-5)";
    return [
      {
        label: `${featureLabel(key)}${suffix}`,
        value: formatIndicatorValue(key, value),
        source,
        manualTag: manualTagForSource(source),
      },
    ];
  });

  const manualItems = MANUAL_ONLY_INDICATORS.flatMap(({ key, label }) => {
    const value = record.demographics_manual?.[key as keyof NonNullable<typeof record.demographics_manual>];
    if (value == null || Number.isNaN(value)) return [];
    const source = fieldSources[key];
    return [
      {
        label,
        value: formatIndicatorValue(key, value),
        source,
        manualTag: "Manual",
      },
    ];
  });

  const changeItems = CHANGE_INDICATORS.flatMap(({ key, label }) => {
    const value = record.demographics_change[key as keyof typeof record.demographics_change];
    if (value == null || Number.isNaN(value)) return [];
    const sign = value > 0 ? "+" : "";
    return [{ label, value: `${sign}${value.toFixed(2)}` }];
  });

  const showManualNotice = hasManualLayer || (record.manual_demographic_fields_count ?? 0) > 0;

  return (
    <>
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-medium">Demographic profile</h2>
            <p className="mt-1 text-sm text-muted">
              District-linked NFHS-5 indicators where coverage permits, supplemented by manually sourced public data where noted.
            </p>
          </div>
          <DemographicSourceBadge sourceType={sourceType} />
        </div>

        {showManualNotice ? (
          <div className="mt-4 flex gap-2 rounded-lg border border-warning/30 bg-warning/5 px-3 py-3 text-sm text-muted">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
            <p>
              Some demographic values for this constituency were manually sourced from public documents.
              Manual entries are source-tracked and may use district or state proxies marked with lower confidence.
              Generated pipeline values are preferred when both are available.
            </p>
          </div>
        ) : null}

        {!demo || (nfhs5Items.length === 0 && manualItems.length === 0) ? (
          <div className="mt-4">
            <CoverageWarning message="Election data is available for this constituency, but demographic coverage is not yet available." />
          </div>
        ) : (
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {nfhs5Items.map(({ label, value, source, manualTag }) => (
              <IndicatorCard key={label} label={label} value={value} source={source} manualTag={manualTag} />
            ))}
          </div>
        )}
      </div>

      {manualItems.length > 0 ? (
        <IndicatorGrid
          title="Manually sourced indicators"
          description="Census, religion, literacy, and other fields entered from public sources with explicit provenance."
          items={manualItems}
        />
      ) : null}

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
        {record.demographic_source_type ? (
          <div className="rounded-lg border border-border/80 bg-bg/30 p-3">
            <dt className="text-xs text-muted">Demographic source type</dt>
            <dd className="mt-1 font-medium">
              {DEMOGRAPHIC_SOURCE_LABELS[record.demographic_source_type] || record.demographic_source_type}
            </dd>
          </div>
        ) : null}
        {record.manual_demographic_fields_count != null && record.manual_demographic_fields_count > 0 ? (
          <div className="rounded-lg border border-border/80 bg-bg/30 p-3">
            <dt className="text-xs text-muted">Manual demographic fields</dt>
            <dd className="mt-1 font-medium tabular-nums">{record.manual_demographic_fields_count}</dd>
          </div>
        ) : null}
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
