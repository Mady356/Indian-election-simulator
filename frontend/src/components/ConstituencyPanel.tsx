import { Link } from "react-router-dom";
import { MapPin, ArrowRight } from "lucide-react";
import { DataQualityBadge } from "./DataQualityBadge";
import { CoverageWarning } from "./CoverageWarning";
import type { ConstituencyRecord } from "@/lib/data";
import { hasDemographics } from "@/lib/data";
import {
  formatShare,
  formatSwing,
  normalizeKey,
  partyColor,
  routeConstituencyKey,
  routeStateKey,
} from "@/lib/format";
import { QUALITY_LABELS } from "@/lib/constants";

const EXAMPLE_CONSTITUENCIES = [
  "Varanasi",
  "Wayanad",
  "Mumbai North",
  "Bangalore South",
  "Asansol",
] as const;

function findExample(
  name: string,
  constituencies: ConstituencyRecord[],
): ConstituencyRecord | undefined {
  const key = normalizeKey(name);
  return constituencies.find((c) => normalizeKey(c.constituency) === key);
}

function turnoutChange(record: ConstituencyRecord): number | null {
  if (record.turnout_2019 == null || record.turnout_2024 == null) return null;
  return record.turnout_2024 - record.turnout_2019;
}

function PassportRow({
  label,
  value,
  valueColor,
}: {
  label: string;
  value: string;
  valueColor?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-border/50 py-2.5 last:border-0">
      <span className="text-xs text-muted">{label}</span>
      <span className="text-right text-sm font-medium tabular-nums" style={{ color: valueColor }}>
        {value}
      </span>
    </div>
  );
}

interface ConstituencyPanelProps {
  record: ConstituencyRecord | null;
  constituencies?: ConstituencyRecord[];
  onSelect?: (record: ConstituencyRecord) => void;
}

export function ConstituencyPanel({
  record,
  constituencies = [],
  onSelect,
}: ConstituencyPanelProps) {
  if (!record) {
    const examples = EXAMPLE_CONSTITUENCIES.map((name) => ({
      name,
      record: findExample(name, constituencies),
    })).filter((e) => e.record);

    return (
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <MapPin className="h-5 w-5" />
        </div>
        <h2 className="mt-4 text-lg font-semibold">Start exploring</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          Search for a constituency or click the map to open its election profile.
        </p>
        {examples.length > 0 ? (
          <div className="mt-4">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted">
              Featured constituencies
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {examples.map(({ name, record: ex }) => (
                <button
                  key={name}
                  type="button"
                  onClick={() => ex && onSelect?.(ex)}
                  className="rounded-full border border-border bg-bg px-3 py-1.5 text-xs text-text transition hover:border-primary/50 hover:bg-primary/10 hover:text-primary"
                >
                  {name}
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  const demo = hasDemographics(record);
  const tChange = turnoutChange(record);
  const coveragePct =
    record.nfhs5_coverage_share != null
      ? formatShare(record.nfhs5_coverage_share * 100)
      : "N/A";

  return (
    <div className="space-y-4 rounded-xl border border-border bg-card p-5">
      <div className="border-b border-border pb-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-primary">
              Constituency profile
            </p>
            <h2 className="mt-1 text-xl font-semibold leading-tight">{record.constituency}</h2>
            <p className="mt-0.5 text-sm text-muted">{record.state}</p>
          </div>
          <DataQualityBadge label={record.data_quality_label} />
        </div>
      </div>

      <div className="rounded-lg border border-border/80 bg-bg/40 px-3 py-1">
        <PassportRow
          label="Winner 2019"
          value={record.winner_party_2019 || "N/A"}
          valueColor={partyColor(record.winner_party_2019)}
        />
        <PassportRow
          label="Winner 2024"
          value={record.winner_party_2024 || "N/A"}
          valueColor={partyColor(record.winner_party_2024)}
        />
        <PassportRow
          label="BJP vote share"
          value={`${formatShare(record.bjp_vote_share_2019)} → ${formatShare(record.bjp_vote_share_2024)}`}
          valueColor={partyColor("BJP")}
        />
        <PassportRow
          label="INC vote share"
          value={`${formatShare(record.inc_vote_share_2019)} → ${formatShare(record.inc_vote_share_2024)}`}
          valueColor={partyColor("INC")}
        />
        <PassportRow label="BJP swing" value={formatSwing(record.bjp_swing_2019_2024)} />
        <PassportRow label="INC swing" value={formatSwing(record.inc_swing_2019_2024)} />
        <PassportRow
          label="Turnout change"
          value={
            tChange != null
              ? `${tChange > 0 ? "+" : ""}${tChange.toFixed(1)} pp`
              : "N/A"
          }
        />
        <PassportRow label="Demographic coverage" value={coveragePct} />
        {record.districts_used ? (
          <PassportRow label="Districts used" value={record.districts_used} />
        ) : null}
        {record.districts_missing ? (
          <PassportRow label="Districts missing" value={record.districts_missing} />
        ) : null}
      </div>

      {!demo ? (
        <CoverageWarning message="Election data is available for this constituency, but demographic coverage is not yet available." />
      ) : (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
            Demographics (NFHS-5)
          </h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(record.demographics_nfhs5)
              .filter(([, v]) => v != null)
              .slice(0, 4)
              .map(([k, v]) => (
                <div key={k} className="rounded border border-border/70 bg-bg/30 px-2 py-1.5">
                  <div className="text-muted">{k.replace(/_/g, " ")}</div>
                  <div className="font-medium tabular-nums">
                    {typeof v === "number" ? v.toFixed(1) : "N/A"}
                  </div>
                </div>
              ))}
          </div>
          <p className="text-[10px] text-muted">
            Quality: {QUALITY_LABELS[record.data_quality_label] || record.data_quality_label}
          </p>
        </div>
      )}

      <Link
        to={`/constituency/${routeStateKey(record.state_key)}/${routeConstituencyKey(record.constituency_key)}`}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-white transition hover:bg-primary/90"
      >
        Open full profile
        <ArrowRight className="h-4 w-4" />
      </Link>
    </div>
  );
}
