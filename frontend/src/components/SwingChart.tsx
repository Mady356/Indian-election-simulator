import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { COLORS } from "@/lib/constants";

interface SwingChartProps {
  data: Array<{ label: string; y2019?: number | null; y2024?: number | null }>;
  title?: string;
}

export function SwingChart({ data, title }: SwingChartProps) {
  if (!data.length) {
    return <div className="text-sm text-muted">No chart data available.</div>;
  }

  return (
    <div className="h-64 w-full">
      {title ? <h3 className="mb-3 text-sm font-medium">{title}</h3> : null}
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: COLORS.muted, fontSize: 12 }} />
          <YAxis tick={{ fill: COLORS.muted, fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              background: COLORS.card,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 8,
              color: COLORS.text,
            }}
          />
          <Legend />
          <Bar dataKey="y2019" name="2019" fill={COLORS.muted} radius={[4, 4, 0, 0]} />
          <Bar dataKey="y2024" name="2024" fill={COLORS.primary} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface MarginChartProps {
  margin2019?: number | null;
  margin2024?: number | null;
}

export function MarginChart({ margin2019, margin2024 }: MarginChartProps) {
  if (margin2019 == null && margin2024 == null) {
    return (
      <div>
        <h3 className="mb-3 text-sm font-medium">Winning margin (%)</h3>
        <p className="text-sm text-muted">Margin data not available.</p>
      </div>
    );
  }
  const data = [
    { label: "Margin", y2019: margin2019 ?? undefined, y2024: margin2024 ?? undefined },
  ];
  return <SwingChart data={data} title="Winning margin (%)" />;
}

interface TurnoutChartProps {
  turnout2019?: number | null;
  turnout2024?: number | null;
}

export function TurnoutChart({ turnout2019, turnout2024 }: TurnoutChartProps) {
  if (turnout2019 == null && turnout2024 == null) {
    return (
      <div>
        <h3 className="mb-3 text-sm font-medium">Turnout (%)</h3>
        <p className="text-sm text-muted">Turnout data not available.</p>
      </div>
    );
  }
  const data = [
    { label: "Turnout", y2019: turnout2019 ?? undefined, y2024: turnout2024 ?? undefined },
  ];
  return <SwingChart data={data} title="Turnout (%)" />;
}

interface VoteShareChartProps {
  bjp2019?: number | null;
  bjp2024?: number | null;
  inc2019?: number | null;
  inc2024?: number | null;
}

export function VoteShareChart({ bjp2019, bjp2024, inc2019, inc2024 }: VoteShareChartProps) {
  const hasData =
    bjp2019 != null || bjp2024 != null || inc2019 != null || inc2024 != null;
  if (!hasData) {
    return (
      <div>
        <h3 className="mb-3 text-sm font-medium">BJP / INC vote share (%)</h3>
        <p className="text-sm text-muted">Vote share data not available.</p>
      </div>
    );
  }
  const data = [
    { label: "BJP", y2019: bjp2019 ?? undefined, y2024: bjp2024 ?? undefined },
    { label: "INC", y2019: inc2019 ?? undefined, y2024: inc2024 ?? undefined },
  ];
  return <SwingChart data={data} title="BJP / INC vote share (%)" />;
}
