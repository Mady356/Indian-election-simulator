import { Link } from "react-router-dom";
import { ArrowLeftRight } from "lucide-react";
import { DataQualityBadge } from "./DataQualityBadge";
import type { ConstituencyRecord } from "@/lib/data";
import { buildConstituencySummary } from "@/lib/constituencySummary";
import { partyColor, routeStateKey } from "@/lib/format";
import { QUALITY_LABELS } from "@/lib/constants";

export function ConstituencyHero({ record }: { record: ConstituencyRecord }) {
  const isElectionOnly = record.data_quality_label === "election_only";
  const flipped = Boolean(record.winner_changed);
  const winnerParty = record.winner_party_2024 || "N/A";

  return (
    <section className="rounded-xl border border-border bg-gradient-to-br from-card via-card to-primary/5 p-5 md:p-6">
      <p className="text-sm text-muted">
        <Link to="/" className="hover:text-primary">
          Explore
        </Link>{" "}
        /{" "}
        <Link to={`/state/${routeStateKey(record.state_key)}`} className="hover:text-primary">
          {record.state}
        </Link>{" "}
        / Constituency passport
      </p>

      <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">{record.constituency}</h1>
          <p className="mt-1 text-sm font-medium text-primary">{record.state}</p>
          <p className="mt-3 text-sm leading-relaxed text-muted">{buildConstituencySummary(record)}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {isElectionOnly ? (
            <span className="inline-flex items-center rounded-full border border-border bg-bg/60 px-2.5 py-0.5 text-xs font-medium text-muted">
              Election-only profile
            </span>
          ) : null}
          <DataQualityBadge label={record.data_quality_label} />
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-3">
        <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted">2024 winner</p>
          <p className="mt-1 text-lg font-semibold" style={{ color: partyColor(winnerParty) }}>
            {winnerParty}
          </p>
          {record.winner_2024 ? (
            <p className="mt-0.5 text-xs text-muted">{record.winner_2024}</p>
          ) : null}
        </div>
        <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted">Seat status</p>
          <p className="mt-1 flex items-center gap-1.5 text-lg font-semibold">
            {flipped ? (
              <>
                <ArrowLeftRight className="h-4 w-4 text-warning" />
                <span className="text-warning">Flipped</span>
              </>
            ) : (
              <span className="text-accent">Held</span>
            )}
          </p>
          <p className="mt-0.5 text-xs text-muted">
            {flipped
              ? `${record.winner_party_2019 || "?"} → ${record.winner_party_2024 || "?"}`
              : `Retained by ${winnerParty}`}
          </p>
        </div>
        <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted">Data quality</p>
          <p className="mt-1 text-lg font-semibold">
            {QUALITY_LABELS[record.data_quality_label] || record.data_quality_label}
          </p>
        </div>
      </div>
    </section>
  );
}
