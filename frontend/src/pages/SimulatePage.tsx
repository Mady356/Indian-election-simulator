import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { IndiaMap } from "@/components/map/IndiaMap";
import { Card, SectionTitle, StatCard, Badge } from "@/components/ui/Card";
import { api } from "@/services/api";
import { partyColor } from "@/lib/utils";
import { Play, Sparkles } from "lucide-react";
import type { SimulationRequest } from "@/types";

interface SliderControlProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
}

function SliderControl({
  label,
  value,
  onChange,
  min = -10,
  max = 10,
  step = 0.5,
}: SliderControlProps) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <label className="text-xs font-medium text-muted">{label}</label>
        <span className="text-xs font-semibold text-primary">
          {value >= 0 ? "+" : ""}
          {value.toFixed(1)}pp
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full accent-primary"
      />
    </div>
  );
}

export function SimulatePage() {
  const [bjpSwing, setBjpSwing] = useState(0);
  const [incSwing, setIncSwing] = useState(0);
  const [urbanEffect, setUrbanEffect] = useState(0.05);
  const [femaleEduEffect, setFemaleEduEffect] = useState(0.03);
  const [fertilityEffect, setFertilityEffect] = useState(0);
  const [internetEffect, setInternetEffect] = useState(0);

  const mutation = useMutation({
    mutationFn: (body: SimulationRequest) => api.simulate(body),
  });

  const runSimulation = () => {
    const body: SimulationRequest = {
      base_year: 2024,
      party_swings: {},
      variable_effects: {},
    };
    if (bjpSwing !== 0) body.party_swings.BJP = bjpSwing;
    if (incSwing !== 0) body.party_swings.INC = incSwing;
    if (urbanEffect !== 0) {
      body.variable_effects.urban_pct = { party: "BJP", effect_per_unit: urbanEffect };
    }
    if (femaleEduEffect !== 0) {
      body.variable_effects.female_literacy_pct = {
        party: "INC",
        effect_per_unit: femaleEduEffect,
      };
    }
    if (fertilityEffect !== 0) {
      body.variable_effects.fertility_rate = {
        party: "BJP",
        effect_per_unit: fertilityEffect,
      };
    }
    mutation.mutate(body);
  };

  const result = mutation.data;

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-border px-6 py-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <div>
            <h1 className="text-lg font-semibold text-text">Simulate</h1>
            <p className="text-sm text-muted">Project seat outcomes with swings & demographics</p>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-72 shrink-0 overflow-y-auto border-r border-border p-5 space-y-5">
          <SectionTitle title="National Swings" subtitle="Uniform vote share shift" />
          <SliderControl label="BJP Swing" value={bjpSwing} onChange={setBjpSwing} />
          <SliderControl label="INC Swing" value={incSwing} onChange={setIncSwing} />

          <SectionTitle title="Demographic Effects" subtitle="Per-unit impact on party share" />
          <SliderControl
            label="Urbanization → BJP"
            value={urbanEffect}
            onChange={setUrbanEffect}
            min={0}
            max={0.2}
            step={0.01}
          />
          <SliderControl
            label="Female Education → INC"
            value={femaleEduEffect}
            onChange={setFemaleEduEffect}
            min={0}
            max={0.2}
            step={0.01}
          />
          <SliderControl
            label="Fertility → BJP"
            value={fertilityEffect}
            onChange={setFertilityEffect}
            min={0}
            max={0.2}
            step={0.01}
          />

          <button
            type="button"
            onClick={runSimulation}
            disabled={mutation.isPending}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-3 text-sm font-semibold text-white shadow-glow transition hover:bg-primary/90 disabled:opacity-50"
          >
            <Play className="h-4 w-4" />
            {mutation.isPending ? "Running..." : "Run Simulation"}
          </button>

          {mutation.isError && (
            <p className="text-xs text-red-400">
              Simulation failed. Is the backend running on port 8000?
            </p>
          )}
        </aside>

        <div className="relative flex-1 p-4">
          <IndiaMap
            mode="constituency"
            selectedState={null}
            onStateClick={() => {}}
            onDistrictClick={() => {}}
            onConstituencyClick={() => {}}
            className="h-full w-full rounded-xl border border-border"
          />
        </div>

        <aside className="w-80 shrink-0 overflow-y-auto border-l border-border p-5 space-y-4">
          {!result && (
            <Card>
              <p className="text-sm text-muted">
                Adjust controls and run a simulation to see projected seat totals and flips.
              </p>
            </Card>
          )}

          {result && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <StatCard
                  label="Seats Changed"
                  value={String(result.seats_changed)}
                  accent
                />
                <StatCard
                  label="Projected"
                  value={String(result.constituencies_projected)}
                />
              </div>

              <Card glow>
                <SectionTitle title="Projected Seat Totals" />
                <div className="space-y-2">
                  {Object.entries(result.projected_seat_totals)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 8)
                    .map(([party, seats]) => (
                      <div
                        key={party}
                        className="flex items-center justify-between rounded-lg bg-bg/40 px-3 py-2"
                      >
                        <Badge color={partyColor(party)}>{party}</Badge>
                        <span className="text-lg font-semibold text-text">{seats}</span>
                      </div>
                    ))}
                </div>
              </Card>

              {result.sample_changes.length > 0 && (
                <Card>
                  <SectionTitle title="Changed Seats" subtitle="Sample flips" />
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {result.sample_changes.slice(0, 10).map((c) => (
                      <div
                        key={c.constituency_id}
                        className="rounded-lg bg-bg/40 px-3 py-2"
                      >
                        <p className="text-sm font-medium text-text">{c.constituency}</p>
                        <p className="text-xs text-muted">{c.state}</p>
                        <p className="mt-1 text-xs">
                          <span className="text-muted">{c.base_winner}</span>
                          {" → "}
                          <span className="text-accent">{c.projected_winner}</span>
                        </p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
