import type { ConstituencyRecord } from "./data";

export interface StateMovements {
  bjpGains: ConstituencyRecord[];
  bjpLosses: ConstituencyRecord[];
  incGains: ConstituencyRecord[];
  incLosses: ConstituencyRecord[];
  closest2024: ConstituencyRecord[];
  flipped: ConstituencyRecord[];
}

export function computeStateMovements(constituencies: ConstituencyRecord[]): StateMovements {
  const bjpGains = [...constituencies]
    .filter((c) => c.bjp_swing_2019_2024 != null && c.bjp_swing_2019_2024 > 0)
    .sort((a, b) => (b.bjp_swing_2019_2024 ?? 0) - (a.bjp_swing_2019_2024 ?? 0))
    .slice(0, 10);

  const bjpLosses = [...constituencies]
    .filter((c) => c.bjp_swing_2019_2024 != null && c.bjp_swing_2019_2024 < 0)
    .sort((a, b) => (a.bjp_swing_2019_2024 ?? 0) - (b.bjp_swing_2019_2024 ?? 0))
    .slice(0, 10);

  const incGains = [...constituencies]
    .filter((c) => c.inc_swing_2019_2024 != null && c.inc_swing_2019_2024 > 0)
    .sort((a, b) => (b.inc_swing_2019_2024 ?? 0) - (a.inc_swing_2019_2024 ?? 0))
    .slice(0, 10);

  const incLosses = [...constituencies]
    .filter((c) => c.inc_swing_2019_2024 != null && c.inc_swing_2019_2024 < 0)
    .sort((a, b) => (a.inc_swing_2019_2024 ?? 0) - (b.inc_swing_2019_2024 ?? 0))
    .slice(0, 10);

  const closest2024 = [...constituencies]
    .filter((c) => c.margin_2024 != null)
    .sort((a, b) => (a.margin_2024 ?? 999) - (b.margin_2024 ?? 999))
    .slice(0, 10);

  const flipped = [...constituencies]
    .filter((c) => c.winner_changed)
    .sort((a, b) => a.constituency.localeCompare(b.constituency));

  return { bjpGains, bjpLosses, incGains, incLosses, closest2024, flipped };
}
