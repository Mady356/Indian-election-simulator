import { APP_NAME } from "@/lib/constants";
import type { CoverageSummary } from "@/lib/data";
import { formatNumber } from "@/lib/format";

interface ExploreHeroProps {
  coverage: CoverageSummary;
}

function HeroStat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-border/80 bg-bg/40 px-4 py-3">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted">{label}</div>
      <div className="mt-1 text-xl font-semibold tabular-nums text-text">{value}</div>
      {hint ? <div className="mt-0.5 text-[11px] text-muted">{hint}</div> : null}
    </div>
  );
}

export function ExploreHero({ coverage }: ExploreHeroProps) {
  const total = coverage.election_constituencies_total;
  const withDemo = coverage.constituencies_with_demographic_coverage;

  return (
    <section className="rounded-xl border border-border bg-gradient-to-br from-card via-card to-primary/5 p-5 md:p-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">{APP_NAME}</h1>
          <p className="mt-1 text-sm font-medium text-primary md:text-base">
            India&apos;s constituency-level election intelligence platform
          </p>
          <p className="mt-3 text-sm leading-relaxed text-muted md:text-base">
            Explore Lok Sabha results, demographic indicators, swing analysis, and political
            change across all {formatNumber(total)} mapped constituencies.
          </p>
        </div>
        <div className="grid w-full gap-3 sm:grid-cols-3 lg:max-w-xl lg:shrink-0">
          <HeroStat label="Constituencies" value={formatNumber(total)} hint="Lok Sabha seats mapped" />
          <HeroStat
            label="With demographics"
            value={formatNumber(withDemo)}
            hint={
              coverage.demographic_coverage_pct != null
                ? `${coverage.demographic_coverage_pct.toFixed(0)}% coverage`
                : undefined
            }
          />
          <HeroStat label="Election comparison" value="2019 → 2024" hint="Vote share & seat change" />
        </div>
      </div>
    </section>
  );
}
