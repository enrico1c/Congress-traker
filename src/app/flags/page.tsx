import type { Metadata } from "next";
import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { getFlags, getMembers } from "@/lib/data/loader";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import {
  partyBgClass,
  partyShort,
  severityBgClass,
  severityLabel,
  formatDate,
  formatAmountRange,
  tradeTypeBgClass,
} from "@/lib/utils/formatting";

export const metadata: Metadata = {
  title: "Flagged Trades",
  description: "Congressional trades flagged for potential policy-area overlap.",
};

export const revalidate = 21600;

export default function FlagsPage() {
  const flags = getFlags().sort((a, b) => b.overallScore - a.overallScore);

  const critical = flags.filter((f) => f.severity === "critical").length;
  const high     = flags.filter((f) => f.severity === "high").length;
  const medium   = flags.filter((f) => f.severity === "medium").length;
  const low      = flags.filter((f) => f.severity === "low").length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-6 w-6 text-red-400" />
          <h1 className="text-2xl font-bold text-white">Flagged Overlap Trades</h1>
        </div>
        <p className="mt-1 text-sm text-neutral-500">
          Trades where the member's policy area or committee jurisdiction overlaps with the company's sector.
          These are <strong className="text-neutral-300">informational signals only</strong> — not evidence of wrongdoing.
        </p>
      </div>

      {/* Severity breakdown */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Critical (≥75)" value={critical} className="border-red-500/30" />
        <StatCard label="High (≥50)"     value={high}     className="border-orange-500/30" />
        <StatCard label="Medium (≥25)"   value={medium}   className="border-yellow-500/30" />
        <StatCard label="Low (<25)"      value={low} />
      </div>

      {/* Scoring methodology disclaimer */}
      <Card padding="md" className="border-blue-500/20 bg-blue-500/5">
        <h3 className="mb-2 text-sm font-semibold text-white">How Scores Are Calculated</h3>
        <div className="grid gap-2 sm:grid-cols-3 text-xs text-neutral-400">
          <div><strong className="text-neutral-300">Committee jurisdiction</strong> (max 35 pts) — serves on committee with direct industry oversight</div>
          <div><strong className="text-neutral-300">Policy area match</strong> (max 25 pts) — member's tagged policy areas overlap with company sector</div>
          <div><strong className="text-neutral-300">Sector concentration</strong> (max 15 pts) — repeated trades in same relevant sector</div>
          <div><strong className="text-neutral-300">Trade size</strong> (max 10 pts) — larger reported amounts score higher</div>
          <div><strong className="text-neutral-300">Recency</strong> (max 10 pts) — recent trades near legislative activity</div>
          <div><strong className="text-neutral-300">Late disclosure</strong> (max 5 pts) — filed after the 45-day STOCK Act window</div>
        </div>
      </Card>

      {/* Flags table */}
      <div className="overflow-x-auto rounded-lg border border-surface-border">
        <table className="w-full text-left">
          <thead className="border-b border-surface-border bg-surface-muted">
            <tr>
              {["Score","Member","Ticker","Type","Amount","Policy Match","Committees","Trade Date","Summary"].map((h) => (
                <th key={h} className="px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {flags.map((flag, i) => (
              <tr
                key={flag.tradeId}
                className={`border-b border-surface-border/50 hover:bg-surface-raised/50 transition-colors border-l-2 ${
                  flag.severity === "critical" ? "border-l-red-500"    :
                  flag.severity === "high"     ? "border-l-orange-500" :
                  flag.severity === "medium"   ? "border-l-yellow-500" :
                  "border-l-neutral-600"
                } ${i % 2 === 0 ? "" : "bg-surface-muted/20"}`}
              >
                {/* Score */}
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <span className={`text-sm font-bold ${
                      flag.severity === "critical" ? "text-red-400"    :
                      flag.severity === "high"     ? "text-orange-400" :
                      flag.severity === "medium"   ? "text-yellow-400" :
                      "text-neutral-400"
                    }`}>
                      {flag.overallScore}
                    </span>
                    <Badge className={severityBgClass(flag.severity)} size="sm">
                      {severityLabel(flag.severity)}
                    </Badge>
                  </div>
                </td>
                {/* Member */}
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <Badge className={partyBgClass(flag.memberName as never)} size="sm">?</Badge>
                    <Link href={`/members/${flag.memberSlug}`} className="text-xs font-medium text-white hover:text-brand-400">
                      {flag.memberName}
                    </Link>
                  </div>
                </td>
                {/* Ticker */}
                <td className="px-3 py-2.5">
                  <Link href={`/companies/${flag.ticker}`} className="font-mono text-sm font-bold text-brand-400 hover:text-brand-300">
                    {flag.ticker}
                  </Link>
                </td>
                {/* Type */}
                <td className="px-3 py-2.5">
                  <Badge className={tradeTypeBgClass(flag.tradeType)} size="sm">
                    {flag.tradeType.includes("Purchase") ? "BUY" : "SELL"}
                  </Badge>
                </td>
                {/* Amount */}
                <td className="px-3 py-2.5 text-xs text-neutral-400 whitespace-nowrap">
                  {formatAmountRange(flag.amount)}
                </td>
                {/* Policy areas */}
                <td className="px-3 py-2.5">
                  <div className="flex flex-wrap gap-1">
                    {flag.matchedPolicyAreas.slice(0, 2).map((pa) => (
                      <Badge key={pa} className="bg-orange-500/20 text-orange-300 border-orange-500/30" size="sm">
                        {pa.split(" ")[0]}
                      </Badge>
                    ))}
                  </div>
                </td>
                {/* Committees */}
                <td className="px-3 py-2.5 text-xs text-neutral-500 max-w-40 truncate">
                  {flag.matchedCommittees.map((c) => c.name).join(", ") || "—"}
                </td>
                {/* Date */}
                <td className="px-3 py-2.5 text-xs text-neutral-400 whitespace-nowrap">
                  {formatDate(flag.tradeDate)}
                </td>
                {/* Summary */}
                <td className="px-3 py-2.5 text-xs text-neutral-400 max-w-60">{flag.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
