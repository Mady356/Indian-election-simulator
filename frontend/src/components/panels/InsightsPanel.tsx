import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Badge, Card, LoadingDots, Placeholder, SectionTitle, StatCard } from "@/components/ui/Card";
import {
  useConstituency,
  useConstituencyDemographics,
  useConstituencyResults,
  useDistrict,
} from "@/hooks/useApi";
import { useApp } from "@/context/AppContext";
import { formatPct, partyColor, titleCase } from "@/lib/utils";
import { Lightbulb } from "lucide-react";

function InsightLine({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg bg-primary/5 px-3 py-2">
      <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
      <p className="text-xs leading-relaxed text-muted">{text}</p>
    </div>
  );
}

export function InsightsPanel() {
  const {
    selectedDistrictId,
    selectedConstituencyId,
    selectedState,
    selectedDistrictName,
    selectedConstituencyName,
    mapMode,
  } = useApp();

  const { data: district, isLoading: districtLoading } = useDistrict(selectedDistrictId);
  const { data: constituency, isLoading: constituencyLoading } = useConstituency(
    selectedConstituencyId,
  );
  const { data: demographics } = useConstituencyDemographics(selectedConstituencyId);
  const { data: results } = useConstituencyResults(selectedConstituencyId);

  if (!selectedDistrictId && !selectedConstituencyId) {
    return (
      <div className="flex h-full flex-col p-6">
        <h2 className="text-lg font-semibold text-text">Insights</h2>
        <p className="mt-1 text-sm text-muted">
          Select a region on the map to explore election and demographic intelligence.
        </p>
        <div className="mt-8 flex flex-1 items-center justify-center">
          <Placeholder message="Click a state, district, or constituency on the map" />
        </div>
      </div>
    );
  }

  const demo = demographics?.demographics || district?.demographics?.[0];
  const results2019 = results?.results?.["2019"] || [];
  const results2024 = results?.results?.["2024"] || [];
  const summary2019 = constituency?.election_history?.find((h) => h.year === 2019);
  const summary2024 = constituency?.election_history?.find((h) => h.year === 2024);

  const chartData = results2024.slice(0, 5).map((r) => ({
    party: r.party,
    share: r.vote_share || 0,
  }));

  const insights: string[] = [];
  if (demo?.urban_pct != null && demo.urban_pct > 45) {
    insights.push("Urban population significantly above national average.");
  }
  if (demo?.female_literacy_pct != null && demo.female_literacy_pct > 70) {
    insights.push("Female literacy among the highest quartile nationally.");
  }
  if (summary2019 && summary2024 && summary2019.winner_party !== summary2024.winner_party) {
    insights.push(
      `Seat flipped from ${summary2019.winner_party} (2019) to ${summary2024.winner_party} (2024).`,
    );
  }
  if (summary2024?.margin_pct != null && summary2024.margin_pct < 3) {
    insights.push("Extremely competitive seat — margin under 3% in 2024.");
  }

  const loading =
    (selectedConstituencyId && constituencyLoading) ||
    (selectedDistrictId && !selectedConstituencyId && districtLoading);

  return (
    <div className="flex h-full flex-col overflow-y-auto p-5 space-y-4 animate-slide-up">
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-muted">
          {selectedState}
        </p>
        <h2 className="text-xl font-semibold text-text">
          {titleCase(
            selectedConstituencyName || selectedDistrictName || selectedState || "",
          )}
        </h2>
        <p className="mt-0.5 text-xs text-muted capitalize">{mapMode} view</p>
      </div>

      {loading && <LoadingDots />}

      {selectedConstituencyId && summary2024 && (
        <Card glow>
          <SectionTitle title="Election Snapshot" subtitle="Lok Sabha 2019 → 2024" />
          <div className="grid grid-cols-2 gap-3">
            <StatCard
              label="Winner 2019"
              value={summary2019?.winner_party || "—"}
              sub={formatPct(summary2019?.winner_vote_share)}
            />
            <StatCard
              label="Winner 2024"
              value={summary2024.winner_party || "—"}
              sub={formatPct(summary2024.winner_vote_share)}
              accent
            />
            <StatCard
              label="Margin 2024"
              value={formatPct(summary2024.margin_pct)}
              sub={`${(summary2024.margin_votes || 0).toLocaleString("en-IN")} votes`}
            />
            <StatCard
              label="Runner-up"
              value={summary2024.runner_up_party || "—"}
            />
          </div>
        </Card>
      )}

      {demo && (
        <Card>
          <SectionTitle title="Demographic Snapshot" subtitle={demo.survey || "NFHS"} />
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Urban" value={formatPct(demo.urban_pct)} />
            <StatCard label="Female Literacy" value={formatPct(demo.female_literacy_pct)} />
            <StatCard label="Electricity" value={formatPct(demo.electricity_pct)} />
            <StatCard label="Fertility Rate" value={demo.fertility_rate?.toFixed(1) || "—"} />
          </div>
        </Card>
      )}

      {constituency?.districts && constituency.districts.length > 0 && (
        <Card>
          <SectionTitle title="District Composition" />
          <div className="space-y-2">
            {constituency.districts.map((d) => (
              <div
                key={d.district_id}
                className="flex items-center justify-between rounded-lg bg-bg/40 px-3 py-2"
              >
                <span className="text-sm text-text">{d.district}</span>
                <Badge>{formatPct((d.district_segment_share || 0) * 100)}</Badge>
              </div>
            ))}
          </div>
        </Card>
      )}

      {chartData.length > 0 && (
        <Card>
          <SectionTitle title="2024 Vote Share" />
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 8 }}>
              <XAxis type="number" hide domain={[0, 100]} />
              <YAxis type="category" dataKey="party" width={48} tick={{ fill: "#94A3B8", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "#131A2D",
                  border: "1px solid #1E2942",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(v: number) => [`${v.toFixed(1)}%`, "Share"]}
              />
              <Bar dataKey="share" radius={[0, 4, 4, 0]}>
                {chartData.map((entry) => (
                  <Cell key={entry.party} fill={partyColor(entry.party)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      {insights.length > 0 && (
        <Card>
          <SectionTitle title="Key Insights" />
          <div className="space-y-2">
            {insights.map((text) => (
              <InsightLine key={text} text={text} />
            ))}
          </div>
        </Card>
      )}

      {!loading && !demo && !summary2024 && (
        <Placeholder message="Limited data available for this selection. Try a mapped constituency." />
      )}
    </div>
  );
}
