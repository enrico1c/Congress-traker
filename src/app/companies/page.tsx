import type { Metadata } from "next";
import Link from "next/link";
import { getCompanies } from "@/lib/data/loader";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { AlertTriangle } from "lucide-react";

export const metadata: Metadata = {
  title: "Companies",
  description: "All companies traded by members of Congress.",
};

export const revalidate = 21600;

export default function CompaniesPage() {
  const companies = getCompanies().sort((a, b) => b.tradeCount - a.tradeCount);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Traded Companies</h1>
        <p className="mt-1 text-sm text-neutral-500">
          {companies.length} companies · sorted by trade frequency
        </p>
      </div>

      <div className="overflow-x-auto rounded-lg border border-surface-border">
        <table className="w-full text-left">
          <thead className="border-b border-surface-border bg-surface-muted">
            <tr>
              {["Ticker","Company","Sector","Industry","Trades","Members","Buys","Sells","Flagged"].map((h) => (
                <th key={h} className="px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {companies.map((co, i) => (
              <tr
                key={co.ticker}
                className={`border-b border-surface-border/50 hover:bg-surface-raised/50 transition-colors ${
                  i % 2 === 0 ? "" : "bg-surface-muted/20"
                }`}
              >
                <td className="px-3 py-2.5">
                  <Link
                    href={`/companies/${co.ticker}`}
                    className="font-mono text-sm font-bold text-brand-400 hover:text-brand-300"
                  >
                    {co.ticker}
                  </Link>
                </td>
                <td className="px-3 py-2.5">
                  <Link href={`/companies/${co.ticker}`} className="text-sm text-white hover:text-brand-400 max-w-48 block truncate">
                    {co.name}
                  </Link>
                </td>
                <td className="px-3 py-2.5">
                  <Badge className="bg-surface border-surface-border text-neutral-400" size="sm">
                    {co.sector}
                  </Badge>
                </td>
                <td className="px-3 py-2.5 text-xs text-neutral-500 max-w-36 truncate">{co.industry}</td>
                <td className="px-3 py-2.5 text-xs font-mono font-bold text-white">{co.tradeCount}</td>
                <td className="px-3 py-2.5 text-xs font-mono text-neutral-400">{co.uniqueTraders}</td>
                <td className="px-3 py-2.5 text-xs font-mono text-gain">{co.buyCount}</td>
                <td className="px-3 py-2.5 text-xs font-mono text-loss">{co.sellCount}</td>
                <td className="px-3 py-2.5">
                  {co.flaggedTradeCount > 0 ? (
                    <div className="flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3 text-red-400" />
                      <span className="text-xs text-red-400">{co.flaggedTradeCount}</span>
                    </div>
                  ) : (
                    <span className="text-xs text-neutral-600">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
