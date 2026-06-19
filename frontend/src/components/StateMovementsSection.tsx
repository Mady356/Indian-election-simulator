import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import type { ConstituencyRecord } from "@/lib/data";
import type { StateMovements } from "@/lib/stateMovements";
import { formatShare, formatSwing, routeConstituencyKey, routeStateKey } from "@/lib/format";

function MovementTable({
  title,
  subtitle,
  rows,
  stateKey,
  renderExtra,
  emptyMessage,
}: {
  title: string;
  subtitle?: string;
  rows: ConstituencyRecord[];
  stateKey: string;
  renderExtra: (row: ConstituencyRecord) => ReactNode;
  emptyMessage: string;
}) {
  return (
    <div className="flex h-full flex-col rounded-xl border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h3 className="text-sm font-medium">{title}</h3>
        {subtitle ? <p className="mt-0.5 text-[11px] text-muted">{subtitle}</p> : null}
      </div>
      {rows.length === 0 ? (
        <p className="flex flex-1 items-center px-4 py-6 text-sm text-muted">{emptyMessage}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <tbody>
              {rows.map((row) => (
                <tr key={row.constituency_key} className="border-t border-border/60 first:border-t-0">
                  <td className="px-4 py-2">
                    <Link
                      to={`/constituency/${routeStateKey(stateKey)}/${routeConstituencyKey(row.constituency_key)}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {row.constituency}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums text-muted">{renderExtra(row)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function StateMovementsSection({
  movements,
  stateKey,
}: {
  movements: StateMovements;
  stateKey: string;
}) {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Key state movements</h2>
        <p className="mt-1 text-sm text-muted">
          Largest swings and closest contests within this state (2019 → 2024).
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <MovementTable
          title="Top BJP gains"
          subtitle="Largest positive BJP vote-share swing"
          rows={movements.bjpGains}
          stateKey={stateKey}
          renderExtra={(row) => formatSwing(row.bjp_swing_2019_2024)}
          emptyMessage="No positive BJP swings recorded."
        />
        <MovementTable
          title="Top BJP losses"
          subtitle="Largest negative BJP vote-share swing"
          rows={movements.bjpLosses}
          stateKey={stateKey}
          renderExtra={(row) => formatSwing(row.bjp_swing_2019_2024)}
          emptyMessage="No negative BJP swings recorded."
        />
        <MovementTable
          title="Top INC gains"
          subtitle="Largest positive INC vote-share swing"
          rows={movements.incGains}
          stateKey={stateKey}
          renderExtra={(row) => formatSwing(row.inc_swing_2019_2024)}
          emptyMessage="No positive INC swings recorded."
        />
        <MovementTable
          title="Top INC losses"
          subtitle="Largest negative INC vote-share swing"
          rows={movements.incLosses}
          stateKey={stateKey}
          renderExtra={(row) => formatSwing(row.inc_swing_2019_2024)}
          emptyMessage="No negative INC swings recorded."
        />
        <MovementTable
          title="Closest seats (2024)"
          subtitle="Smallest winning margin in 2024"
          rows={movements.closest2024}
          stateKey={stateKey}
          renderExtra={(row) => formatShare(row.margin_2024)}
          emptyMessage="Margin data not available."
        />
        <MovementTable
          title="Flipped seats"
          subtitle="Winner changed between 2019 and 2024"
          rows={movements.flipped}
          stateKey={stateKey}
          renderExtra={(row) =>
            `${row.winner_party_2019 || "?"} → ${row.winner_party_2024 || "?"}`
          }
          emptyMessage="No seat flips in this state."
        />
      </div>
    </section>
  );
}
