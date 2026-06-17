import { Search } from "lucide-react";
import type { ConstituencyRecord } from "@/lib/data";

interface SearchBoxProps {
  constituencies: ConstituencyRecord[];
  value: string;
  onChange: (value: string) => void;
  onSelect: (record: ConstituencyRecord) => void;
}

export function SearchBox({ constituencies, value, onChange, onSelect }: SearchBoxProps) {
  const q = value.trim().toLowerCase();
  const results =
    q.length < 2
      ? []
      : constituencies
          .filter(
            (c) =>
              c.constituency.toLowerCase().includes(q) ||
              c.state.toLowerCase().includes(q),
          )
          .slice(0, 8);

  return (
    <div className="relative">
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search constituency or state…"
        className="w-full rounded-lg border border-border bg-bg py-2.5 pl-10 pr-3 text-sm outline-none ring-primary/40 placeholder:text-muted focus:ring-2"
      />
      {results.length > 0 && (
        <div className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-lg border border-border bg-card shadow-card">
          {results.map((row) => (
            <button
              key={`${row.state_key}-${row.constituency_key}`}
              type="button"
              onClick={() => {
                onSelect(row);
                onChange("");
              }}
              className="flex w-full flex-col items-start px-3 py-2 text-left text-sm hover:bg-border/40"
            >
              <span className="font-medium">{row.constituency}</span>
              <span className="text-xs text-muted">{row.state}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
