import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { COLORS } from "@/lib/constants";

interface MonteCarloHistogramProps {
  title: string;
  data: Array<{ seats: number; count: number }>;
  median: number;
  p10: number;
  p90: number;
  color?: string;
}

export function MonteCarloHistogram({
  title,
  data,
  median,
  p10,
  p90,
  color = COLORS.primary,
}: MonteCarloHistogramProps) {
  if (!data.length) {
    return (
      <div className="rounded-xl border border-border bg-card p-4">
        <h3 className="text-sm font-medium">{title}</h3>
        <p className="mt-3 text-sm text-muted">No simulation data yet. Run simulations to see the distribution.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <h3 className="text-sm font-medium">{title}</h3>
      <p className="mt-1 text-xs text-muted">
        Median {median} · 10th–90th percentile: {p10}–{p90}
      </p>
      <div className="mt-3 h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="seats" tick={{ fill: COLORS.muted, fontSize: 11 }} />
            <YAxis tick={{ fill: COLORS.muted, fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                background: COLORS.card,
                border: `1px solid ${COLORS.border}`,
                borderRadius: 8,
                color: COLORS.text,
              }}
              formatter={(value: number) => [`${value} simulations`, "Count"]}
              labelFormatter={(label) => `${label} seats`}
            />
            <ReferenceLine x={median} stroke={COLORS.accent} strokeDasharray="4 4" />
            <Bar dataKey="count" fill={color} radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
