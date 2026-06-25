import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, Info, Play, RotateCcw } from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { MonteCarloHistogram } from "@/components/MonteCarloHistogram";
import { VolatileSeatsTable } from "@/components/VolatileSeatsTable";
import { PageError, PageLoader } from "@/components/Layout";
import { COLORS } from "@/lib/constants";
import {
  ALLIANCE_COLORS,
  defaultMonteCarloInputs,
  formatProbability,
  formatSwingLabel,
  loadMonteCarloBase,
  percentile,
  runMonteCarloElection,
  type MonteCarloInputs,
  type MonteCarloResult,
} from "@/lib/monteCarlo";
import { formatNumber } from "@/lib/format";

const SIM_COUNTS = [100, 1000, 5000, 10000] as const;

function SwingSlider({
  label,
  value,
  onChange,
  min,
  max,
  step = 0.5,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
}) {
  return (
    <div className="rounded-lg border border-border/80 bg-bg/30 p-3">
      <div className="flex items-center justify-between gap-2">
        <label className="text-xs font-medium">{label}</label>
        <span className="text-xs font-semibold tabular-nums text-primary">{formatSwingLabel(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="mt-2 w-full accent-primary"
      />
    </div>
  );
}

function SigmaSlider({
  label,
  value,
  onChange,
  max,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  max: number;
}) {
  return (
    <div className="rounded-lg border border-border/80 bg-bg/30 p-3">
      <div className="flex items-center justify-between gap-2">
        <label className="text-xs font-medium">{label}</label>
        <span className="text-xs font-semibold tabular-nums text-muted">σ {value.toFixed(1)}</span>
      </div>
      <input
        type="range"
        min={0}
        max={max}
        step={0.5}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="mt-2 w-full accent-primary"
      />
    </div>
  );
}

export function ForecastPage() {
  const { data: base, isLoading, isError, error } = useQuery({
    queryKey: ["monte-carlo-base"],
    queryFn: loadMonteCarloBase,
    staleTime: 5 * 60 * 1000,
  });

  const [inputs, setInputs] = useState<MonteCarloInputs>(defaultMonteCarloInputs());
  const [result, setResult] = useState<MonteCarloResult | null>(null);
  const [running, setRunning] = useState(false);

  const states = useMemo(() => {
    if (!base) return [];
    return [...new Set(base.constituencies.map((c) => c.state))].sort();
  }, [base]);

  const runSimulations = () => {
    if (!base) return;
    setRunning(true);
    window.setTimeout(() => {
      const output = runMonteCarloElection(base, inputs);
      setResult(output);
      setRunning(false);
    }, 0);
  };

  const resetAssumptions = () => {
    setInputs(defaultMonteCarloInputs());
    setResult(null);
  };

  const downloadSummary = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result.detail, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `the543-monte-carlo-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) return <PageLoader />;
  if (isError || !base) {
    return (
      <PageError
        message={
          error?.message ||
          "Monte Carlo base data is unavailable. Run python -m src.simulation.build_monte_carlo_base and refresh."
        }
      />
    );
  }

  const summary = result?.summary;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <section className="rounded-xl border border-border bg-gradient-to-br from-card via-card to-primary/5 p-5 md:p-6">
        <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Forecast Lab</h1>
        <p className="mt-2 text-sm text-muted md:text-base">
          Run Monte Carlo simulations of India&apos;s Lok Sabha map.
        </p>
        <p className="mt-3 rounded-lg border border-warning/30 bg-warning/10 px-4 py-3 text-sm leading-relaxed text-muted">
          This is an experimental simulator, not a prediction. It starts from 2024 constituency
          results and applies user-controlled uncertainty assumptions. Polling and CSDS-Lokniti
          calibration will be added later.
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-4">
            <h2 className="text-sm font-semibold">Simulation controls</h2>

            <div className="mt-3">
              <label className="text-xs font-medium text-muted">Number of simulations</label>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {SIM_COUNTS.map((count) => (
                  <button
                    key={count}
                    type="button"
                    onClick={() => setInputs((prev) => ({ ...prev, numSimulations: count }))}
                    className={[
                      "rounded-lg border px-2 py-2 text-xs",
                      inputs.numSimulations === count
                        ? "border-primary bg-primary/15 text-primary"
                        : "border-border text-muted hover:text-text",
                    ].join(" ")}
                  >
                    {formatNumber(count)}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 space-y-2">
              <SwingSlider label="NDA/BJP swing" value={inputs.ndaSwing} onChange={(v) => setInputs((p) => ({ ...p, ndaSwing: v }))} min={-10} max={10} />
              <SwingSlider label="INDIA/INC swing" value={inputs.indiaSwing} onChange={(v) => setInputs((p) => ({ ...p, indiaSwing: v }))} min={-10} max={10} />
              <SwingSlider label="Others swing" value={inputs.othersSwing} onChange={(v) => setInputs((p) => ({ ...p, othersSwing: v }))} min={-10} max={10} />
            </div>

            <div className="mt-4 space-y-2">
              <SigmaSlider label="National uncertainty" value={inputs.nationalSigma} onChange={(v) => setInputs((p) => ({ ...p, nationalSigma: v }))} max={8} />
              <SigmaSlider label="State uncertainty" value={inputs.stateSigma} onChange={(v) => setInputs((p) => ({ ...p, stateSigma: v }))} max={10} />
              <SigmaSlider label="Seat uncertainty" value={inputs.seatSigma} onChange={(v) => setInputs((p) => ({ ...p, seatSigma: v }))} max={15} />
            </div>

            <div className="mt-4 space-y-3">
              <div>
                <label className="text-xs font-medium text-muted">State filter</label>
                <select
                  value={inputs.stateFilter || ""}
                  onChange={(e) => setInputs((p) => ({ ...p, stateFilter: e.target.value || null }))}
                  className="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm"
                >
                  <option value="">All states</option>
                  {states.map((state) => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </select>
              </div>

              <label className="flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={inputs.onlySelectedState}
                  onChange={(e) => setInputs((p) => ({ ...p, onlySelectedState: e.target.checked }))}
                  className="mt-1 accent-primary"
                />
                <span>Only simulate selected state</span>
              </label>

              <label className="flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={inputs.includeLowConfidence}
                  onChange={(e) => setInputs((p) => ({ ...p, includeLowConfidence: e.target.checked }))}
                  className="mt-1 accent-primary"
                />
                <span>Include low-confidence seats</span>
              </label>

              <div>
                <label className="text-xs font-medium text-muted">Random seed (optional)</label>
                <input
                  type="number"
                  value={inputs.seed ?? ""}
                  onChange={(e) =>
                    setInputs((p) => ({
                      ...p,
                      seed: e.target.value ? parseInt(e.target.value, 10) : null,
                    }))
                  }
                  placeholder="Auto"
                  className="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="mt-4 flex flex-col gap-2">
              <button
                type="button"
                onClick={runSimulations}
                disabled={running}
                className="flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-white transition hover:bg-primary/90 disabled:opacity-60"
              >
                <Play className="h-4 w-4" />
                {running ? "Running…" : "Run simulations"}
              </button>
              <button
                type="button"
                onClick={resetAssumptions}
                className="flex items-center justify-center gap-2 rounded-lg border border-border bg-bg px-4 py-2.5 text-sm transition hover:border-primary/40"
              >
                <RotateCcw className="h-4 w-4" />
                Reset assumptions
              </button>
            </div>
          </div>
        </aside>

        <div className="space-y-6">
          {!summary ? (
            <div className="rounded-xl border border-border bg-card p-8 text-center text-sm text-muted">
              Configure assumptions and click <strong className="text-text">Run simulations</strong> to generate Monte Carlo seat distributions.
            </div>
          ) : (
            <>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <MetricCard label="NDA/BJP plurality probability" value={formatProbability(summary.nda_plurality_probability)} accent="accent" />
                <MetricCard label="INDIA/INC plurality probability" value={formatProbability(summary.india_plurality_probability)} accent="primary" />
                <MetricCard label="Others/regional plurality probability" value={formatProbability(summary.others_plurality_probability)} />
                <MetricCard label="NDA/BJP majority probability" value={formatProbability(summary.nda_majority_probability)} accent="accent" hint="≥272 seats" />
                <MetricCard label="INDIA/INC majority probability" value={formatProbability(summary.india_majority_probability)} accent="primary" hint="≥272 seats" />
                <MetricCard label="Hung parliament probability" value={formatProbability(summary.hung_parliament_probability)} accent="warning" />
                <MetricCard label="Median NDA/BJP seats" value={summary.median_nda_seats} hint={`80% range ${summary.nda_seat_p10}–${summary.nda_seat_p90}`} />
                <MetricCard label="Median INDIA/INC seats" value={summary.median_india_seats} hint={`80% range ${summary.india_seat_p10}–${summary.india_seat_p90}`} />
                <MetricCard label="Median Others seats" value={summary.median_others_seats} />
                <MetricCard label="Volatile seats" value={summary.volatile_seat_count} hint={`${formatNumber(summary.simulations_run)} simulations run`} accent="danger" />
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                <MonteCarloHistogram
                  title="NDA/BJP seat distribution"
                  data={result.nda_seat_distribution}
                  median={summary.median_nda_seats}
                  p10={summary.nda_seat_p10}
                  p90={summary.nda_seat_p90}
                  color={ALLIANCE_COLORS.NDA}
                />
                <MonteCarloHistogram
                  title="INDIA/INC seat distribution"
                  data={result.india_seat_distribution}
                  median={summary.median_india_seats}
                  p10={summary.india_seat_p10}
                  p90={summary.india_seat_p90}
                  color={ALLIANCE_COLORS.INDIA}
                />
                <MonteCarloHistogram
                  title="Others seat distribution"
                  data={result.others_seat_distribution}
                  median={summary.median_others_seats}
                  p10={percentileFromHistogram(result.others_seat_distribution, 0.1)}
                  p90={percentileFromHistogram(result.others_seat_distribution, 0.9)}
                  color={COLORS.muted}
                />
              </div>

              <VolatileSeatsTable rows={result.volatile_seats} />

              <button
                type="button"
                onClick={downloadSummary}
                className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2.5 text-sm transition hover:border-primary/40 hover:text-primary"
              >
                <Download className="h-4 w-4" />
                Download simulation summary JSON
              </button>
            </>
          )}
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-start gap-3">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
            <div>
              <h2 className="font-medium">How this works</h2>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted">
                <li>Starts from 2024 constituency results in the Monte Carlo base dataset.</li>
                <li>Applies national, state-level, and seat-level uncertainty each simulation.</li>
                <li>Runs many possible elections and counts resulting alliance seat totals.</li>
                <li>Uncertainty sliders are user-controlled and not calibrated to current polling.</li>
                <li>Not calibrated to current polling yet and not a causal model.</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="font-medium">Coming later</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-muted">
            <li>CSDS-Lokniti vote-bank calibration</li>
            <li>Pre-poll vs post-poll polling error</li>
            <li>State-level polling inputs</li>
            <li>Candidate/incumbency adjustments</li>
            <li>Probabilistic model calibration</li>
          </ul>
        </div>
      </section>
    </div>
  );
}

function percentileFromHistogram(
  data: Array<{ seats: number; count: number }>,
  p: number,
): number {
  const expanded: number[] = [];
  for (const row of data) {
    for (let i = 0; i < row.count; i += 1) expanded.push(row.seats);
  }
  return percentile([...expanded].sort((a, b) => a - b), p);
}
