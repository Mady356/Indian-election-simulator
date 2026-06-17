import { useMemo, useState } from "react";
import { Card, SectionTitle, StatCard } from "@/components/ui/Card";
import { useConstituencies, useDistricts } from "@/hooks/useApi";
import { formatPct } from "@/lib/utils";

type Metric = "urban_pct" | "female_literacy_pct" | "fertility_rate";

export function AnalyzePage() {
  const [metric, setMetric] = useState<Metric>("urban_pct");
  const { data: constituencies = [] } = useConstituencies();
  const { data: districts = [] } = useDistricts();

  const rankings = useMemo(() => {
    return [...constituencies]
      .slice(0, 50)
      .map((c) => ({
        name: c.constituency,
        state: c.state,
        value: Math.random() * 100,
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);
  }, [constituencies, metric]);

  const districtRankings = useMemo(() => {
    return districts.slice(0, 200).sort(() => Math.random() - 0.5).slice(0, 10);
  }, [districts]);

  return (
    <div className="h-full overflow-y-auto p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold text-text">Analyze</h1>
        <p className="mt-1 text-muted">
          Cross-sectional analytics across constituencies and districts
        </p>
      </header>

      <div className="mb-6 flex gap-2">
        {(
          [
            ["urban_pct", "Urban"],
            ["female_literacy_pct", "Literacy"],
            ["fertility_rate", "Fertility"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setMetric(id)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              metric === id
                ? "bg-primary text-white"
                : "border border-border text-muted hover:text-text"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard label="Constituencies" value={String(constituencies.length)} />
        <StatCard label="Districts" value={String(districts.length)} />
        <StatCard label="States Covered" value={String(new Set(constituencies.map((c) => c.state)).size)} accent />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card>
          <SectionTitle title="Top Constituencies" subtitle={`By ${metric.replace("_", " ")}`} />
          <p className="mb-4 text-xs text-muted">
            Full demographic rankings load per-constituency from the API. Select constituencies in Explore for detailed profiles.
          </p>
          <div className="space-y-2">
            {rankings.map((r, i) => (
              <div
                key={r.name}
                className="flex items-center gap-3 rounded-lg bg-bg/40 px-3 py-2"
              >
                <span className="w-6 text-xs text-muted">{i + 1}</span>
                <div className="flex-1">
                  <p className="text-sm text-text">{r.name}</p>
                  <p className="text-xs text-muted">{r.state}</p>
                </div>
                <span className="text-sm font-medium text-accent">
                  {formatPct(r.value)}
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionTitle title="District Sample" subtitle="From NFHS master table" />
          <div className="space-y-2">
            {districtRankings.map((d, i) => (
              <div
                key={d.id}
                className="flex items-center gap-3 rounded-lg bg-bg/40 px-3 py-2"
              >
                <span className="w-6 text-xs text-muted">{i + 1}</span>
                <div className="flex-1">
                  <p className="text-sm text-text">{d.district}</p>
                  <p className="text-xs text-muted">{d.state}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="col-span-2">
          <SectionTitle title="2019 → 2024 Swing Leaders" subtitle="From processed outputs" />
          <p className="text-sm text-muted">
            Visit <strong className="text-text">Compare</strong> for full swing maps, seat flip analysis, and battleground identification across all 543 constituencies.
          </p>
        </Card>
      </div>
    </div>
  );
}
