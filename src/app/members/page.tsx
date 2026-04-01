import type { Metadata } from "next";
import Link from "next/link";
import { getMembers } from "@/lib/data/loader";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import {
  partyBgClass,
  partyShort,
  badgeColorClass,
  formatReturn,
  returnColorClass,
  formatCurrency,
} from "@/lib/utils/formatting";

export const metadata: Metadata = {
  title: "Members",
  description: "All tracked members of Congress and their trading activity.",
};

export const revalidate = 21600;

export default function MembersPage() {
  const members = getMembers().sort((a, b) => b.tradeCount - a.tradeCount);

  const house = members.filter((m) => m.chamber === "House");
  const senate = members.filter((m) => m.chamber === "Senate");

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-white">Members of Congress</h1>
        <p className="mt-1 text-sm text-neutral-500">
          {members.length} tracked members · {house.length} House · {senate.length} Senate
        </p>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "Total Members",      value: members.length },
          { label: "With Flagged Trades", value: members.filter((m) => m.flaggedTradeCount > 0).length },
          { label: "Active Traders",     value: members.filter((m) => m.tradeCount >= 10).length },
          { label: "High Performers",    value: members.filter((m) => m.performanceBadge === "High Outperformance").length },
        ].map((s) => (
          <Card key={s.label} padding="sm">
            <p className="text-xs text-neutral-500">{s.label}</p>
            <p className="mt-1 text-xl font-bold text-white">{s.value}</p>
          </Card>
        ))}
      </div>

      {/* Member table */}
      <div className="overflow-x-auto rounded-lg border border-surface-border">
        <table className="w-full text-left">
          <thead className="border-b border-surface-border bg-surface-muted">
            <tr>
              {["Member","Chamber","State","Policy Areas","Trades","Flagged","Est. 1Y Return","Badge"].map((h) => (
                <th key={h} className="px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {members.map((m, i) => (
              <tr
                key={m.id}
                className={`border-b border-surface-border/50 hover:bg-surface-raised/50 transition-colors ${
                  i % 2 === 0 ? "" : "bg-surface-muted/20"
                }`}
              >
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <Badge className={partyBgClass(m.party)} size="sm">{partyShort(m.party)}</Badge>
                    <Link href={`/members/${m.slug}`} className="text-sm font-medium text-white hover:text-brand-400 transition-colors">
                      {m.name}
                    </Link>
                  </div>
                </td>
                <td className="px-3 py-2.5 text-xs text-neutral-400">{m.chamber}</td>
                <td className="px-3 py-2.5 text-xs text-neutral-400">{m.state}</td>
                <td className="px-3 py-2.5">
                  <div className="flex flex-wrap gap-1">
                    {m.policyAreas.slice(0, 2).map((pa) => (
                      <Badge key={pa} className="bg-surface border-surface-border text-neutral-400" size="sm">
                        {pa.split(" ")[0]}
                      </Badge>
                    ))}
                    {m.policyAreas.length > 2 && (
                      <span className="text-xs text-neutral-600">+{m.policyAreas.length - 2}</span>
                    )}
                  </div>
                </td>
                <td className="px-3 py-2.5 text-xs font-mono text-white">{m.tradeCount}</td>
                <td className="px-3 py-2.5">
                  {m.flaggedTradeCount > 0 ? (
                    <span className="text-xs font-mono text-red-400">{m.flaggedTradeCount}</span>
                  ) : (
                    <span className="text-xs text-neutral-600">—</span>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  <span className={`text-xs font-mono ${returnColorClass(m.estimatedReturn1y)}`}>
                    {formatReturn(m.estimatedReturn1y)}
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  <Badge className={badgeColorClass(m.performanceBadge)} size="sm">
                    {m.performanceBadge.split(" ")[0]}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
