import { NavLink } from "react-router-dom";
import { APP_NAME, APP_SUBTITLE } from "@/lib/constants";
import {
  BarChart3,
  Compass,
  FlaskConical,
  GitCompare,
  LineChart,
  Map,
  Vote,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Explore", icon: Map, enabled: true },
  { to: "/compare", label: "Compare", icon: GitCompare, enabled: true },
  { to: "/forecast", label: "Forecast", icon: LineChart, enabled: true },
  { to: "/insights", label: "Insights Lab", icon: FlaskConical, enabled: true },
  { to: "/methodology", label: "Methodology", icon: BarChart3, enabled: true },
] as const;

const COMING_SOON = [
  { label: "Vote Bank Analysis", description: "CSDS-Lokniti layer pending", icon: Vote },
  { label: "Opinion Poll Lab", description: "Pre-poll vs post-poll comparison", icon: Compass },
] as const;

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-card/60 md:flex">
      <div className="border-b border-border px-5 py-5">
        <h1 className="text-xl font-semibold leading-tight">{APP_NAME}</h1>
        <p className="mt-1 text-xs text-muted">{APP_SUBTITLE}</p>
      </div>
      <nav className="flex flex-1 flex-col gap-1 p-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, enabled }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              [
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition",
                isActive
                  ? "bg-primary/15 text-primary"
                  : "text-muted hover:bg-border/40 hover:text-text",
                !enabled && "pointer-events-none opacity-50",
              ].join(" ")
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
        <div className="mt-4 px-3 text-[10px] font-semibold uppercase tracking-wider text-muted">
          Coming soon
        </div>
        {COMING_SOON.map(({ label, description, icon: Icon }) => (
          <div
            key={label}
            className="rounded-lg px-3 py-2 text-sm text-muted/70"
            title={description}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-3">
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </span>
              <span className="shrink-0 rounded-full bg-border px-2 py-0.5 text-[10px]">Soon</span>
            </div>
            <p className="mt-1 pl-7 text-[11px] leading-snug text-muted/60">{description}</p>
          </div>
        ))}
      </nav>
    </aside>
  );
}
