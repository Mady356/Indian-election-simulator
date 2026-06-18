import { COLORS, QUALITY_LABELS, type MapColorMode } from "@/lib/constants";
import { coverageColor, partyColor } from "@/lib/format";

const WINNER_PARTIES = [
  { label: "BJP", party: "BJP" },
  { label: "INC", party: "INC" },
  { label: "SP", party: "SP" },
  { label: "TDP", party: "TDP" },
  { label: "AITC", party: "AITC" },
  { label: "Other / Regional", party: "Regional" },
] as const;

const SWING_SCALE = [
  { label: "Strong gain (+10 pp+)", color: COLORS.accent },
  { label: "Modest gain", color: "#86EFAC" },
  { label: "Modest loss", color: COLORS.warning },
  { label: "Strong loss", color: COLORS.danger },
] as const;

const COVERAGE_SCALE = [
  { key: "high", label: QUALITY_LABELS.high },
  { key: "medium", label: QUALITY_LABELS.medium },
  { key: "low", label: QUALITY_LABELS.low },
  { key: "election_only", label: QUALITY_LABELS.election_only },
] as const;

export function MapLegend({ mode }: { mode: MapColorMode }) {
  return (
    <div className="pointer-events-none absolute bottom-3 left-3 z-10 max-w-[220px] rounded-lg border border-border bg-card/95 px-3 py-2.5 text-[11px] shadow-card backdrop-blur-sm">
      <div className="mb-1.5 font-semibold uppercase tracking-wide text-muted">
        {mode === "winner_2024" && "Winner 2024"}
        {mode === "bjp_swing" && "BJP swing"}
        {mode === "inc_swing" && "INC swing"}
        {mode === "data_coverage" && "Data coverage"}
      </div>

      {mode === "winner_2024" ? (
        <div className="grid grid-cols-2 gap-x-3 gap-y-1">
          {WINNER_PARTIES.map(({ label, party }) => (
            <div key={label} className="flex items-center gap-1.5">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-sm"
                style={{ backgroundColor: partyColor(party) }}
              />
              <span className="text-text">{label}</span>
            </div>
          ))}
        </div>
      ) : null}

      {mode === "bjp_swing" || mode === "inc_swing" ? (
        <div className="space-y-1">
          {SWING_SCALE.map(({ label, color }) => (
            <div key={label} className="flex items-center gap-2">
              <span className="h-2.5 w-6 shrink-0 rounded-sm" style={{ backgroundColor: color }} />
              <span className="text-muted">{label}</span>
            </div>
          ))}
          <p className="mt-1.5 border-t border-border/60 pt-1.5 text-[10px] text-muted">
            Swing = 2024 vote share minus 2019 vote share (percentage points).
          </p>
        </div>
      ) : null}

      {mode === "data_coverage" ? (
        <div className="space-y-1">
          {COVERAGE_SCALE.map(({ key, label }) => (
            <div key={key} className="flex items-center gap-2">
              <span
                className="h-2.5 w-6 shrink-0 rounded-sm"
                style={{ backgroundColor: coverageColor(key) }}
              />
              <span className="text-muted">{label}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
