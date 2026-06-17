import { Outlet } from "react-router-dom";
import { APP_DISCLAIMER } from "@/lib/constants";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function Layout() {
  return (
    <div className="flex h-full min-h-screen bg-bg text-text">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <main className="flex-1 overflow-auto p-4 md:p-6">
          <Outlet />
        </main>
        <footer className="border-t border-border bg-card/30 px-4 py-4 text-xs leading-relaxed text-muted md:px-6">
          {APP_DISCLAIMER}
        </footer>
      </div>
    </div>
  );
}

export function PageLoader() {
  return (
    <div className="flex h-64 items-center justify-center text-muted">
      Loading dashboard data…
    </div>
  );
}

export function PageError({ message }: { message?: string }) {
  return (
    <div className="rounded-xl border border-danger/40 bg-danger/10 p-6 text-sm text-text">
      <h2 className="mb-2 text-lg font-semibold text-danger">Unable to load data</h2>
      <p className="text-muted">
        {message ||
          "Static JSON files may be missing. Run python -m src.export.build_frontend_data_bundle and refresh."}
      </p>
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-8 text-center">
      <h3 className="text-lg font-medium">{title}</h3>
      <p className="mt-2 text-sm text-muted">{body}</p>
    </div>
  );
}
