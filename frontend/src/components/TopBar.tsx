import { NavLink } from "react-router-dom";
import { APP_DESCRIPTION, APP_SUBTITLE } from "@/lib/constants";

const MOBILE_LINKS = [
  { to: "/", label: "Explore", end: true },
  { to: "/compare", label: "Compare" },
  { to: "/forecast", label: "Forecast" },
  { to: "/insights", label: "Insights" },
  { to: "/essays", label: "Essays" },
  { to: "/methodology", label: "Methodology" },
] as const;

export function TopBar() {
  return (
    <header className="border-b border-border bg-card/40 px-4 py-4 md:px-6">
      <p className="text-sm font-medium text-text">{APP_SUBTITLE}</p>
      <p className="mt-1 max-w-3xl text-sm text-muted">{APP_DESCRIPTION}</p>
      <nav className="mt-3 flex gap-2 overflow-x-auto md:hidden">
        {MOBILE_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={"end" in link ? link.end : undefined}
            className={({ isActive }) =>
              [
                "shrink-0 rounded-full border px-3 py-1 text-xs",
                isActive
                  ? "border-primary bg-primary/15 text-primary"
                  : "border-border text-muted",
              ].join(" ")
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
