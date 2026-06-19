import type { ReactNode } from "react";
import type { SeatAnalysisRecord } from "@/lib/seatAnalysis";
import { analysisSourceLabel, formatKeyFactor, parseKeyFactors } from "@/lib/seatAnalysis";

function NoteSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-border/80 bg-bg/30 p-4">
      <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted">{title}</h3>
      <div className="mt-2 text-sm leading-relaxed text-text">{children}</div>
    </div>
  );
}

function SourceBadge({ source }: { source: SeatAnalysisRecord["analysis_source"] }) {
  const label = analysisSourceLabel(source);
  const isGenerated = source === "generated";
  const badgeClass = isGenerated
    ? "border-border bg-bg/50 text-muted"
    : "border-primary/30 bg-primary/10 text-primary";

  return (
    <div className="space-y-1">
      <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${badgeClass}`}>
        {label}
      </span>
      <p className="text-[11px] text-muted">
        {isGenerated
          ? "This note is generated from structured election and demographic data."
          : "This note includes analyst-reviewed content."}
      </p>
    </div>
  );
}

function ConfidenceBadge({ confidence }: { confidence: string }) {
  const normalized = confidence.toLowerCase();
  const tone =
    normalized === "high"
      ? "text-accent border-accent/30 bg-accent/10"
      : normalized === "low"
        ? "text-warning border-warning/30 bg-warning/10"
        : "text-primary border-primary/30 bg-primary/10";

  return (
    <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${tone}`}>
      {confidence} confidence
    </span>
  );
}

interface SeatIntelligenceCardProps {
  analysis?: SeatAnalysisRecord | null;
}

export function SeatIntelligenceCard({ analysis }: SeatIntelligenceCardProps) {
  if (!analysis) {
    return (
      <section className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-lg font-semibold">Seat Intelligence</h2>
        <p className="mt-3 text-sm text-muted">
          Seat intelligence note is not available for this constituency yet.
        </p>
      </section>
    );
  }

  const factors = parseKeyFactors(analysis.key_factors);

  return (
    <section className="rounded-xl border border-border bg-card p-5 md:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">
            Seat Intelligence
          </p>
          <h2 className="mt-1 text-lg font-semibold">Analytical note</h2>
          <p className="mt-1 text-sm text-muted">
            Structured election and demographic interpretation for this seat.
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <SourceBadge source={analysis.analysis_source} />
          <ConfidenceBadge confidence={analysis.confidence} />
        </div>
      </div>

      {factors.length > 0 ? (
        <div className="mt-4">
          <h3 className="text-[10px] font-semibold uppercase tracking-wider text-muted">Key factors</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {factors.map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-border bg-bg/50 px-2.5 py-1 text-xs text-text"
              >
                {formatKeyFactor(tag)}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <NoteSection title="Analyst summary">{analysis.summary}</NoteSection>
        <NoteSection title="Electoral movement">{analysis.electoral_movement}</NoteSection>
        <NoteSection title="Demographic context">{analysis.demographic_context}</NoteSection>
        <NoteSection title="District context">{analysis.district_context}</NoteSection>
        {analysis.local_context?.trim() ? (
          <NoteSection title="Local context">{analysis.local_context}</NoteSection>
        ) : null}
        <NoteSection title="What to watch">{analysis.what_to_watch}</NoteSection>
        <NoteSection title="Data quality note">{analysis.data_quality_note}</NoteSection>
      </div>

      <p className="mt-4 rounded-lg border border-border/60 bg-bg/30 px-3 py-3 text-xs leading-relaxed text-muted">
        Seat Intelligence notes separate observed electoral movement from interpretation. Missing
        demographic values are not imputed, and descriptive relationships are not causal claims.
      </p>
    </section>
  );
}
