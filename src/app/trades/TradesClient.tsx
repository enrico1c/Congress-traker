"use client";

import { useState, useMemo } from "react";
import { FilterBar } from "@/components/filters/FilterBar";
import { TradeTable } from "@/components/trades/TradeTable";
import type { Trade, TradeFilters } from "@/lib/types";

interface TradesClientProps {
  trades: Trade[];
}

export function TradesClient({ trades }: TradesClientProps) {
  const [filters, setFilters] = useState<TradeFilters>({});

  const filtered = useMemo(() => {
    return trades.filter((t) => {
      if (filters.query) {
        const q = filters.query.toLowerCase();
        if (
          !t.memberName.toLowerCase().includes(q) &&
          !t.ticker.toLowerCase().includes(q) &&
          !t.companyName.toLowerCase().includes(q)
        )
          return false;
      }
      if (filters.chamber && t.memberChamber !== filters.chamber) return false;
      if (filters.party && t.memberParty !== filters.party) return false;
      if (filters.state && t.memberState !== filters.state) return false;
      if (filters.sector && t.sector !== filters.sector) return false;
      if (filters.tradeType && t.tradeType !== filters.tradeType) return false;
      if (filters.dateFrom && t.tradeDate < filters.dateFrom) return false;
      if (filters.dateTo && t.tradeDate > filters.dateTo) return false;
      if (filters.flaggedOnly && !t.isFlagged) return false;
      if (filters.memberId && t.memberId !== filters.memberId) return false;
      if (filters.ticker && t.ticker !== filters.ticker.toUpperCase()) return false;
      return true;
    });
  }, [trades, filters]);

  return (
    <div className="space-y-4">
      <FilterBar
        filters={filters}
        onChange={setFilters}
        totalCount={trades.length}
        filteredCount={filtered.length}
      />
      <TradeTable trades={filtered} />
    </div>
  );
}
