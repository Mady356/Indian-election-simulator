import {
  BarChart3,
  Compass,
  GitCompare,
  LineChart,
  Search,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import clsx from "clsx";
import { useApp } from "@/context/AppContext";

const navItems = [
  { to: "/", icon: Compass, label: "Explore" },
  { to: "/analyze", icon: BarChart3, label: "Analyze" },
  { to: "/simulate", icon: Sparkles, label: "Simulate" },
  { to: "/compare", icon: GitCompare, label: "Compare" },
  { to: "/forecast", icon: TrendingUp, label: "Forecast", soon: true },
];

export function Sidebar() {
  const { setCommandPaletteOpen } = useApp();

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-border bg-card/50">
      <div className="border-b border-border px-5 py-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/20">
            <LineChart className="h-4 w-4 text-primary" />
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-widest text-muted">
              Intelligence
            </p>
            <p className="text-sm font-semibold leading-tight text-text">
              Indian Election
            </p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map(({ to, icon: Icon, label, soon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-primary/15 text-primary shadow-glow"
                  : "text-muted hover:bg-border/30 hover:text-text",
                soon && "opacity-60",
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="flex-1">{label}</span>
            {soon && (
              <span className="rounded bg-border px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted">
                Soon
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-border p-4">
        <button
          type="button"
          onClick={() => setCommandPaletteOpen(true)}
          className="flex w-full items-center gap-2 rounded-lg border border-border bg-bg/50 px-3 py-2.5 text-sm text-muted transition hover:border-primary/40 hover:text-text"
        >
          <Search className="h-4 w-4" />
          <span className="flex-1 text-left">Search...</span>
          <kbd className="rounded border border-border px-1.5 py-0.5 text-[10px]">
            ⌘K
          </kbd>
        </button>
      </div>
    </aside>
  );
}
