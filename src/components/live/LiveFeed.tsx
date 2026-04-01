"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { RefreshCw, AlertTriangle, Wifi, WifiOff } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import type { LiveTrade, LiveResponse } from "@/app/api/live/route";

const POLL_INTERVAL_MS = 60_000;

function partyColor(party: string): string {
  if (party === "Democrat" || party === "D") return "bg-blue-500/20 text-blue-300 border-blue-500/30";
  if (party === "Republican" || party === "R") return "bg-red-500/20 text-red-300 border-red-500/30";
  return "bg-neutral-500/20 text-neutral-300 border-neutral-500/30";
}

function partyShort(party: string): string {
  if (party === "Democrat" || party === "D") return "D";
  if (party === "Republican" || party === "R") return "R";
  return "I";
}

function tradeColor(type: string): string {
  if (type.toLowerCase().includes("purchase")) return "bg-gain/20 text-gain border-gain/30";
  if (type.toLowerCase().includes("sale") || type.toLowerCase().includes("sell"))
    return "bg-loss/20 text-loss border-loss/30";
  return "bg-neutral-500/20 text-neutral-400 border-neutral-500/30";
}

function tradeLabel(type: string): string {
  if (type.toLowerCase().includes("purchase")) return "BUY";
  if (type.toLowerCase().includes("sale") || type.toLowerCase().includes("sell")) return "SELL";
  return type.slice(0, 4).toUpperCase() || "—";
}

function timeAgo(isoStr: string): string {
  const diff = Date.now() - new Date(isoStr).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function formatDate(iso: string): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

export function LiveFeed() {
  const [data, setData] = useState<LiveResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  // tick forces re-render so "X ago" stays current
  const [, setTick] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const refresh = useCallback(async (manual = false) => {
    if (manual) setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/live", { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: LiveResponse = await res.json();
      setData(json);
      setLastRefresh(new Date());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    intervalRef.current = setInterval(() => refresh(), POLL_INTERVAL_MS);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [refresh]);

  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 10_000);
    return () => clearInterval(t);
  }, []);

  const isOnline = !error && data !== null;

  return (
    <Card padding="md">
      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isOnline ? (
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-400" />
            </span>
          ) : (
            <WifiOff className="h-3.5 w-3.5 text-red-400" />
          )}
          <h2 className="text-sm font-semibold text-white">Live Senate Feed</h2>
          <span className="rounded border border-green-500/30 bg-green-500/10 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-green-400">
            Live
          </span>
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-[11px] text-neutral-500">
              {timeAgo(lastRefresh.toISOString())}
            </span>
          )}
          <button
            onClick={() => refresh(true)}
            disabled={loading}
            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-neutral-400 hover:bg-white/5 hover:text-white disabled:opacity-40"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      <p className="mb-3 text-[11px] text-neutral-600">
        Senate EFTS · last 60 days · auto-refreshes every 60s
        {data?.total != null && (
          <>
            {" · "}
            <span className="text-neutral-500">{data.total.toLocaleString()} total</span>
          </>
        )}
      </p>

      {error && (
        <div className="flex items-center gap-2 rounded border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-300">
          <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
          Senate EFTS unavailable — {error}
        </div>
      )}

      {loading && !data && (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-10 animate-pulse rounded bg-white/5" />
          ))}
        </div>
      )}

      {data && data.trades.length > 0 && (
        <div className="divide-y divide-white/5">
          {data.trades.map((trade) => (
            <LiveTradeRow key={trade.id} trade={trade} />
          ))}
        </div>
      )}

      {data && data.trades.length === 0 && !error && (
        <p className="py-6 text-center text-xs text-neutral-500">
          No Senate disclosures found in the last 60 days.
        </p>
      )}
    </Card>
  );
}

function LiveTradeRow({ trade }: { trade: LiveTrade }) {
  const tickerLink = trade.ticker ? `/companies/${trade.ticker}` : null;

  return (
    <div className="flex items-center gap-2 py-2.5 text-xs">
      <Badge className={`${partyColor(trade.party)} flex-shrink-0`} size="sm">
        {partyShort(trade.party)}
      </Badge>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className="truncate font-medium text-white">{trade.memberName}</span>
          {trade.state && (
            <span className="flex-shrink-0 text-neutral-600">({trade.state})</span>
          )}
        </div>
        <div className="flex items-center gap-1.5 text-neutral-400">
          {tickerLink ? (
            <Link href={tickerLink} className="font-mono text-brand-400 hover:text-brand-300">
              {trade.ticker}
            </Link>
          ) : (
            <span className="truncate">{trade.assetName || "—"}</span>
          )}
          {trade.amount && (
            <>
              <span className="text-neutral-600">·</span>
              <span>{trade.amount}</span>
            </>
          )}
        </div>
      </div>

      <Badge className={`${tradeColor(trade.tradeType)} flex-shrink-0`} size="sm">
        {tradeLabel(trade.tradeType)}
      </Badge>

      <span className="hidden flex-shrink-0 text-neutral-500 sm:block">
        {formatDate(trade.disclosureDate || trade.tradeDate)}
      </span>
    </div>
  );
}
