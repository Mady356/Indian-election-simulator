import { Link } from "react-router-dom";
import { DataQualityBadge } from "./DataQualityBadge";
import { CoverageWarning } from "./CoverageWarning";
import { MetricCard } from "./MetricCard";
import type { ConstituencyRecord } from "@/lib/data";
import {
  formatShare,
  formatSwing,
  partyColor,
  routeConstituencyKey,
  routeStateKey,
} from "@/lib/format";
import { hasDemographics } from "@/lib/data";

export function ConstituencyPanel({ record }: { record: ConstituencyRecord | null }) {
  if (!record) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 text-sm text-muted">
        Click a constituency on the map or search to view its profile.
      </div>
    );
  }

  const demo = hasDemographics(record);

  return (
    <div className="space-y-4 rounded-xl border border-border bg-card p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">{record.constituency}</h2>
          <p className="text-sm text-muted">{record.state}</p>
        </div>
        <DataQualityBadge label={record.data_quality_label} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="Winner 2019" value={record.winner_party_2019 || "N/A"} />
        <MetricCard label="Winner 2024" value={record.winner_party_2024 || "N/A"} accent="accent" />
        <MetricCard label="BJP swing" value={formatSwing(record.bjp_swing_2019_2024)} />
        <MetricCard label="INC swing" value={formatSwing(record.inc_swing_2019_2024)} />
      </div>

      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className="rounded-lg border border-border p-3">
          <div className="text-xs text-muted">BJP share</div>
          <div className="mt-1 font-medium" style={{ color: partyColor("BJP") }}>
            {formatShare(record.bjp_vote_share_2019)} → {formatShare(record.bjp_vote_share_2024)}
          </div>
        </div>
        <div className="rounded-lg border border-border p-3">
          <div className="text-xs text-muted">INC share</div>
          <div className="mt-1 font-medium" style={{ color: partyColor("INC") }}>
            {formatShare(record.inc_vote_share_2019)} → {formatShare(record.inc_vote_share_2024)}
          </div>
        </div>
        <div className="rounded-lg border border-border p-3">
          <div className="text-xs text-muted">Margin 2024</div>
          <div className="mt-1 font-medium">{formatShare(record.margin_2024)}</div>
        </div>
        <div className="rounded-lg border border-border p-3">
          <div className="text-xs text-muted">Turnout</div>
          <div className="mt-1 font-medium">
            {formatShare(record.turnout_2019)} → {formatShare(record.turnout_2024)}
          </div>
        </div>
      </div>

      {!demo ? (
        <CoverageWarning message="Election data is available for this constituency, but demographic coverage is not yet available." />
      ) : (
        <div className="space-y-2">
          <h3 className="text-sm font-medium">Demographics (NFHS-5)</h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(record.demographics_nfhs5)
              .filter(([, v]) => v != null)
              .slice(0, 6)
              .map(([k, v]) => (
                <div key={k} className="rounded border border-border/70 px-2 py-1.5">
                  <div className="text-muted">{k.replace(/_/g, " ")}</div>
                  <div className="font-medium">{typeof v === "number" ? v.toFixed(1) : "N/A"}</div>
                </div>
              ))}
          </div>
          {record.districts_used ? (
            <p className="text-xs text-muted">Districts used: {record.districts_used}</p>
          ) : null}
          {record.districts_missing ? (
            <p className="text-xs text-warning">Districts missing: {record.districts_missing}</p>
          ) : null}
        </div>
      )}

      <Link
        to={`/constituency/${routeStateKey(record.state_key)}/${routeConstituencyKey(record.constituency_key)}`}
        className="inline-flex text-sm font-medium text-primary hover:underline"
      >
        Open full constituency profile →
      </Link>
    </div>
  );
}
