import type { Metadata } from "next";
import Link from "next/link";
import { TrendingUp } from "lucide-react";
import { getPerformanceSnapshots, getMemberById } from "@/lib/data/loader";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import {
  badgeColorClass,
  returnColorClass,
  formatReturn,
  partyBgClass,
  partyShort,
} from "@/lib/utils/formatting";

export const metadata: Metadata = {
  title: "Top Performers",
  description: "Members of Congress with the strongest estimated portfolio returns.",
};

export const revalidate = parseInt(process.env.NEXT_REVALIDATE_SECONDS ?? "21600");

export default function PerformersPage() {
  const snapshots = getPerformanceSnapshots()
    .filter((p) => p.estimatedReturn1y !== undefined)
    .sort((a, b) => (b.estimatedReturn1y ?? -999) - (a.estimatedReturn1y ?? -999));

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <TrendingUp className="h-7 w-7 text-brand-400" />
        <div>
          <h1 className="text-2xl font-bold text-white">Portfolio Performers</h1>
          <p className="mt-0.5 text-sm text-neutral-500">
            Estimated returns based on reconstructed portfolios from STOCK Act disclosures.
          </p>
        </div>
      </div>

      {/* Important disclaimer */}
      <Card padding="md" className="border-yellow-500/20 bg-yellow-500/5">
        <h3 className="mb-2 text-sm font-semibold text-yellow-300">Methodology Disclaimer</h3>
        <p className="text-xs text-yellow-300/80 leading-relaxed">
          Portfolio returns shown here are <strong>estimates only</strong>, reconstructed from public STOCK Act
          disclosures. Disclosures use value ranges (not exact amounts), may be filed up to 45 days after the
          trade, and represent only disclosed equity transactions — not full portfolio holdings.
          Returns are calculated using the midpoint of reported value ranges, Yahoo Finance historical prices,
          and a simplified buy-and-hold model. <strong>These figures are not audited and carry significant
          uncertainty. Do not use them for financial decisions.</strong>
        </p>
      </Card>

      {/* Performers table */}
      <div className="overflow-x-auto rounded-lg border border-surface-border">
        <table className="w-full text-left">
          <thead className="border-b border-surface-border bg-surface-muted">
            <tr>
              {["Rank","Member","Badge","Est. 1Y","S&P 1Y","Excess 1Y","Est. 3Y","Est. 5Y","Confidence","Trades"].map((h) => (
                <th key={h} className="px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {snapshots.map((snap, i) => {
              const member = getMemberById(snap.memberId);
              return (
                <tr
                  key={snap.memberId}
                  className={`border-b border-surface-border/50 hover:bg-surface-raised/50 transition-colors ${
                    i % 2 === 0 ? "" : "bg-surface-muted/20"
                  }`}
                >
                  <td className="px-3 py-2.5 text-sm font-bold text-neutral-500">#{i + 1}</td>
                  <td className="px-3 py-2.5">
                    <div className="flex items-center gap-2">
                      {member && (
                        <Badge className={partyBgClass(member.party)} size="sm">
                          {partyShort(member.party)}
                        </Badge>
                      )}
                      <Link
                        href={`/members/${snap.memberSlug}`}
                        className="text-sm font-medium text-white hover:text-brand-400"
                      >
                        {snap.memberName}
                      </Link>
                    </div>
                  </td>
                  <td className="px-3 py-2.5">
                    <Badge className={badgeColorClass(snap.badge)} size="sm">{snap.badge}</Badge>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`text-sm font-bold font-mono ${returnColorClass(snap.estimatedReturn1y)}`}>
                      {formatReturn(snap.estimatedReturn1y)}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-xs font-mono text-neutral-500">
                    {formatReturn(snap.spReturn1y)}
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`text-xs font-mono font-bold ${returnColorClass(snap.excessReturn1y)}`}>
                      {formatReturn(snap.excessReturn1y)}
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`text-xs font-mono ${returnColorClass(snap.estimatedReturn3y)}`}>
                      {formatReturn(snap.estimatedReturn3y)}
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`text-xs font-mono ${returnColorClass(snap.estimatedReturn5y)}`}>
                      {formatReturn(snap.estimatedReturn5y)}
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    <Badge
                      className={
                        snap.confidence === "high"   ? "bg-green-500/20 text-green-300 border-green-500/30" :
                        snap.confidence === "medium" ? "bg-yellow-500/20 text-yellow-300 border-yellow-500/30" :
                        "bg-neutral-500/20 text-neutral-400 border-neutral-500/30"
                      }
                      size="sm"
                    >
                      {snap.confidence}
                    </Badge>
                  </td>
                  <td className="px-3 py-2.5 text-xs font-mono text-neutral-400">{snap.tradeCount}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
