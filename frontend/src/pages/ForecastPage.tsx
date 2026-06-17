import { TrendingUp } from "lucide-react";
import { Placeholder } from "@/components/ui/Card";

export function ForecastPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8">
      <div className="max-w-md text-center animate-slide-up">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/15">
          <TrendingUp className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-2xl font-semibold text-text">Forecast</h1>
        <p className="mt-3 text-muted">
          Probabilistic seat forecasts, scenario ensembles, and confidence intervals — coming in Milestone 2.
        </p>
        <div className="mt-8">
          <Placeholder message="Use Simulate for swing-based projections today" />
        </div>
      </div>
    </div>
  );
}
