"use client";

import { useState } from "react";
import { Filter, X, ChevronDown } from "lucide-react";
import { clsx } from "clsx";
import { SearchInput } from "@/components/ui/SearchInput";
import { POLICY_AREAS } from "@/lib/types";
import type { TradeFilters, Chamber, Party } from "@/lib/types";

const US_STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
  "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
  "VA","WA","WV","WI","WY","DC",
];

const SECTORS = [
  "Technology","Healthcare","Financials","Energy","Industrials","Consumer Discretionary",
  "Consumer Staples","Materials","Real Estate","Utilities","Communication Services",
  "Defense & Aerospace",
];

interface FilterBarProps {
  filters: TradeFilters;
  onChange: (filters: TradeFilters) => void;
  totalCount: number;
  filteredCount: number;
}

export function FilterBar({ filters, onChange, totalCount, filteredCount }: FilterBarProps) {
  const [open, setOpen] = useState(false);

  const activeFilterCount = Object.entries(filters).filter(
    ([k, v]) => k !== "query" && v !== undefined && v !== "" && v !== false
  ).length;

  function set<K extends keyof TradeFilters>(key: K, value: TradeFilters[K]) {
    onChange({ ...filters, [key]: value || undefined });
  }

  function clearAll() {
    onChange({ query: filters.query });
  }

  return (
    <div className="space-y-3">
      {/* Search + filter toggle row */}
      <div className="flex items-center gap-2">
        <SearchInput
          value={filters.query ?? ""}
          onChange={(v) => set("query", v)}
          placeholder="Search member, ticker, company…"
          className="flex-1"
        />
        <button
          onClick={() => setOpen(!open)}
          className={clsx(
            "flex items-center gap-1.5 rounded-md border px-3 py-2 text-xs font-medium transition-colors",
            open || activeFilterCount > 0
              ? "border-brand-500/60 bg-brand-600/20 text-brand-300"
              : "border-surface-border bg-surface-muted text-neutral-400 hover:text-white"
          )}
        >
          <Filter className="h-3.5 w-3.5" />
          Filters
          {activeFilterCount > 0 && (
            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-brand-600 text-white text-xs">
              {activeFilterCount}
            </span>
          )}
          <ChevronDown className={clsx("h-3.5 w-3.5 transition-transform", open && "rotate-180")} />
        </button>
        {activeFilterCount > 0 && (
          <button
            onClick={clearAll}
            className="flex items-center gap-1 text-xs text-neutral-500 hover:text-white"
          >
            <X className="h-3 w-3" />
            Clear
          </button>
        )}
      </div>

      {/* Result count */}
      <p className="text-xs text-neutral-500">
        {filteredCount === totalCount
          ? `${totalCount.toLocaleString()} trades`
          : `${filteredCount.toLocaleString()} of ${totalCount.toLocaleString()} trades`}
      </p>

      {/* Expandable filter panel */}
      {open && (
        <div className="grid grid-cols-2 gap-3 rounded-lg border border-surface-border bg-surface-muted p-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 animate-fade-in">
          <Select
            label="Chamber"
            value={filters.chamber ?? ""}
            onChange={(v) => set("chamber", v as Chamber)}
            options={["", "House", "Senate"]}
            labels={["All Chambers", "House", "Senate"]}
          />
          <Select
            label="Party"
            value={filters.party ?? ""}
            onChange={(v) => set("party", v as Party)}
            options={["", "Democrat", "Republican", "Independent"]}
            labels={["All Parties", "Democrat", "Republican", "Independent"]}
          />
          <Select
            label="State"
            value={filters.state ?? ""}
            onChange={(v) => set("state", v)}
            options={["", ...US_STATES]}
            labels={["All States", ...US_STATES]}
          />
          <Select
            label="Policy Area"
            value={filters.policyArea ?? ""}
            onChange={(v) => set("policyArea", v as TradeFilters["policyArea"])}
            options={["", ...POLICY_AREAS]}
            labels={["All Policy Areas", ...POLICY_AREAS]}
          />
          <Select
            label="Sector"
            value={filters.sector ?? ""}
            onChange={(v) => set("sector", v)}
            options={["", ...SECTORS]}
            labels={["All Sectors", ...SECTORS]}
          />
          <Select
            label="Trade Type"
            value={filters.tradeType ?? ""}
            onChange={(v) => set("tradeType", v as TradeFilters["tradeType"])}
            options={["", "Purchase", "Sale", "Sale (Partial)"]}
            labels={["All Types", "Purchase", "Sale", "Partial Sale"]}
          />
          <div>
            <label className="mb-1 block text-xs text-neutral-500">From</label>
            <input
              type="date"
              value={filters.dateFrom ?? ""}
              onChange={(e) => set("dateFrom", e.target.value)}
              className="w-full rounded border border-surface-border bg-surface px-2 py-1.5 text-xs text-white focus:border-brand-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-neutral-500">To</label>
            <input
              type="date"
              value={filters.dateTo ?? ""}
              onChange={(e) => set("dateTo", e.target.value)}
              className="w-full rounded border border-surface-border bg-surface px-2 py-1.5 text-xs text-white focus:border-brand-500 focus:outline-none"
            />
          </div>
          <div className="flex items-end">
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                checked={filters.flaggedOnly ?? false}
                onChange={(e) => set("flaggedOnly", e.target.checked || undefined)}
                className="h-3.5 w-3.5 rounded border-surface-border bg-surface accent-brand-500"
              />
              <span className="text-xs text-neutral-400">Flagged only</span>
            </label>
          </div>
        </div>
      )}
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
  labels,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  labels: string[];
}) {
  return (
    <div>
      <label className="mb-1 block text-xs text-neutral-500">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded border border-surface-border bg-surface px-2 py-1.5 text-xs text-white focus:border-brand-500 focus:outline-none"
      >
        {options.map((opt, i) => (
          <option key={opt} value={opt}>
            {labels[i]}
          </option>
        ))}
      </select>
    </div>
  );
}
