import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import {
  getCompanies,
  getCompanyByTicker,
  getTradesByTicker,
  getFlags,
} from "@/lib/data/loader";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { TradeTable } from "@/components/trades/TradeTable";
import { AlertTriangle } from "lucide-react";
import { formatDate, partyBgClass, partyShort, severityBgClass, severityLabel } from "@/lib/utils/formatting";

export const revalidate = parseInt(process.env.NEXT_REVALIDATE_SECONDS ?? "21600");

export async function generateStaticParams() {
  return getCompanies().map((c) => ({ ticker: c.ticker }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ ticker: string }>;
}): Promise<Metadata> {
  const { ticker } = await params;
  const co = getCompanyByTicker(ticker);
  if (!co) return { title: "Company Not Found" };
  return { title: `${co.ticker} — ${co.name}`, description: `Congressional trading activity for ${co.name} (${co.ticker}).` };
}

export default async function CompanyPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  const co = getCompanyByTicker(ticker.toUpperCase());
  if (!co) notFound();

  const trades = getTradesByTicker(co.ticker).sort((a, b) =>
    b.disclosureDate.localeCompare(a.disclosureDate)
  );
  const allFlags = getFlags();
  const flags = allFlags
    .filter((f) => f.ticker === co.ticker)
    .sort((a, b) => b.overallScore - a.overallScore);

  // Count unique traders
  const uniqueTraders = [...new Set(trades.map((t) => t.memberId))];

  // Monthly activity
  const monthMap = new Map<string, { buys: number; sells: number }>();
  trades.forEach((t) => {
    const month = t.tradeDate.slice(0, 7);
    const existing = monthMap.get(month) ?? { buys: 0, sells: 0 };
    if (t.tradeType.includes("Purchase")) existing.buys++;
    else existing.sells++;
    monthMap.set(month, existing);
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-3xl font-black text-brand-400">{co.ticker}</span>
            <Badge className="bg-surface border-surface-border text-neutral-400">{co.sector}</Badge>
          </div>
          <h1 className="text-xl font-bold text-white">{co.name}</h1>
          <p className="text-sm text-neutral-500">{co.industry}</p>
        </div>
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="rounded border border-surface-border bg-surface-raised p-3">
            <p className="text-xl font-bold text-white">{co.tradeCount}</p>
            <p className="text-xs text-neutral-500">Total Trades</p>
          </div>
          <div className="rounded border border-surface-border bg-surface-raised p-3">
            <p className="text-xl font-bold text-gain">{co.buyCount}</p>
            <p className="text-xs text-neutral-500">Buys</p>
          </div>
          <div className="rounded border border-surface-border bg-surface-raised p-3">
            <p className="text-xl font-bold text-loss">{co.sellCount}</p>
            <p className="text-xs text-neutral-500">Sells</p>
          </div>
        </div>
      </div>

      {/* Policy areas */}
      {co.policyAreas.length > 0 && (
        <Card padding="sm">
          <p className="mb-2 text-xs text-neutral-500">Related Policy Areas</p>
          <div className="flex flex-wrap gap-1.5">
            {co.policyAreas.map((pa) => (
              <Badge key={pa} className="bg-brand-600/20 text-brand-300 border-brand-500/30" size="sm">
                {pa}
              </Badge>
            ))}
          </div>
        </Card>
      )}

      {/* Flags */}
      {flags.length > 0 && (
        <Card padding="md">
          <div className="mb-3 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <h2 className="text-sm font-semibold text-white">
              Flagged Overlap Trades ({flags.length})
            </h2>
          </div>
          <div className="space-y-2">
            {flags.slice(0, 5).map((flag) => (
              <div
                key={flag.tradeId}
                className="flex items-center justify-between rounded border border-red-500/20 bg-red-500/5 p-2.5"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <Link href={`/members/${flag.memberSlug}`} className="text-sm font-medium text-white hover:text-brand-400">
                      {flag.memberName}
                    </Link>
                    <Badge className={severityBgClass(flag.severity)} size="sm">
                      {severityLabel(flag.severity)}
                    </Badge>
                  </div>
                  <p className="text-xs text-neutral-400 mt-0.5">{flag.summary}</p>
                </div>
                <div className="text-right flex-shrink-0 ml-3">
                  <p className="text-lg font-bold text-red-400">{flag.overallScore}</p>
                  <p className="text-xs text-neutral-500">{formatDate(flag.tradeDate)}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Congressional traders */}
      <Card padding="md">
        <h2 className="mb-3 text-sm font-semibold text-white">
          Congressional Traders ({uniqueTraders.length} members)
        </h2>
        <div className="flex flex-wrap gap-2">
          {uniqueTraders.map((memberId) => {
            const t = trades.find((x) => x.memberId === memberId)!;
            const memberTrades = trades.filter((x) => x.memberId === memberId);
            return (
              <Link
                key={memberId}
                href={`/members/${t.memberSlug}`}
                className="flex items-center gap-1.5 rounded border border-surface-border bg-surface px-2 py-1 hover:border-brand-500/40 transition-colors"
              >
                <Badge className={partyBgClass(t.memberParty)} size="sm">
                  {partyShort(t.memberParty)}
                </Badge>
                <span className="text-xs text-white">{t.memberName}</span>
                <span className="text-xs text-neutral-500">({memberTrades.length})</span>
              </Link>
            );
          })}
        </div>
      </Card>

      {/* Full trade history */}
      <div>
        <h2 className="mb-3 text-lg font-semibold text-white">Trade History ({trades.length})</h2>
        <TradeTable trades={trades} showCompany={false} pageSize={20} />
      </div>
    </div>
  );
}
