import { useNavigate } from "react-router-dom";
import { DataQualityBadge } from "./DataQualityBadge";
import type { ConstituencyRecord } from "@/lib/data";
import { formatShare, formatSwing, routeConstituencyKey, routeStateKey } from "@/lib/format";

export function StateConstituencyTable({
  constituencies,
  stateKey,
}: {
  constituencies: ConstituencyRecord[];
  stateKey: string;
}) {
  const navigate = useNavigate();

  const openConstituency = (record: ConstituencyRecord) => {
    navigate(
      `/constituency/${routeStateKey(stateKey)}/${routeConstituencyKey(record.constituency_key)}`,
    );
  };

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h2 className="font-medium">All constituencies</h2>
        <p className="mt-0.5 text-xs text-muted">
          {constituencies.length} seats · click a row to open the full profile
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-bg/60 text-left text-xs uppercase tracking-wide text-muted">
            <tr>
              <th className="px-4 py-2.5">Constituency</th>
              <th className="px-4 py-2.5">Winner 2019</th>
              <th className="px-4 py-2.5">Winner 2024</th>
              <th className="px-4 py-2.5">BJP swing</th>
              <th className="px-4 py-2.5">INC swing</th>
              <th className="px-4 py-2.5">Margin 2024</th>
              <th className="px-4 py-2.5">Data quality</th>
            </tr>
          </thead>
          <tbody>
            {constituencies.map((c) => (
              <tr
                key={c.constituency_key}
                onClick={() => openConstituency(c)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    openConstituency(c);
                  }
                }}
                tabIndex={0}
                role="link"
                className="cursor-pointer border-t border-border/70 transition hover:bg-primary/5 focus:bg-primary/5 focus:outline-none"
              >
                <td className="px-4 py-2.5 font-medium text-primary">{c.constituency}</td>
                <td className="px-4 py-2.5">{c.winner_party_2019 || "N/A"}</td>
                <td className="px-4 py-2.5">{c.winner_party_2024 || "N/A"}</td>
                <td className="px-4 py-2.5 tabular-nums">{formatSwing(c.bjp_swing_2019_2024)}</td>
                <td className="px-4 py-2.5 tabular-nums">{formatSwing(c.inc_swing_2019_2024)}</td>
                <td className="px-4 py-2.5 tabular-nums">{formatShare(c.margin_2024)}</td>
                <td className="px-4 py-2.5">
                  <DataQualityBadge label={c.data_quality_label} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
