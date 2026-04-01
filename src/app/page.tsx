import Link from "next/link";
import { Activity, AlertTriangle, Users, Building2, TrendingUp } from "lucide-react";
import { getDashboardStats } from "@/lib/data/loader";
import { StatCard } from "@/components/ui/StatCard";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { TradeTimeline } from "@/components/charts/TradeTimeline";
import { PolicyAreaChart } from "@/components/charts/PolicyAreaChart";
import { SectorPieChart } from "@/components/charts/SectorPieChart";
import { LiveFeed } from "@/components/live/LiveFeed";
import {
  partyBgClass,
  partyShort,
  badgeColorClass,
  returnColorClass,
  formatReturn,
} from "@/lib/utils/formatting";

export const revalidate = 21600;

export default function DashboardPage() {
  const stats = getDashboardStats();

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Congressional Trading Dashboard</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Based on STOCK Act public disclosures from the U.S. House and Senate.
          Last updated:{" "}
          <span className="text-neutral-400">
            {stats.lastUpdated
              ? new Date(stats.lastUpdated).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })
              : "—"}
          </span>
        </p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard
          label="Members tracked"
          value={stats.totalMembers.toLocaleString()}
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          label="Total trades"
          value={stats.totalTrades.toLocaleString()}
          icon={<Activity className="h-4 w-4" />}
        />
        <StatCard
          label="Flagged overlaps"
          value={stats.totalFlaggedTrades.toLocaleString()}
          icon={<AlertTriangle className="h-4 w-4" />}
          className="border-red-500/20"
        />
        <StatCard
          label="Companies traded"
          value={stats.totalCompanies.toLocaleString()}
          icon={<Building2 className="h-4 w-4" />}
        />
      </div>

      {/* Live feed — Senate EFTS real-time disclosures */}
      <LiveFeed />

      {/* Trade activity timeline — full width */}
      <Card padding="md">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Trade Activity</h2>
            <p className="text-xs text-neutral-500">Monthly purchases vs sales (historical)</p>
          </div>
          <Link href="/trades" className="text-xs text-brand-400 hover:text-brand-300">
            All trades →
          </Link>
        </div>
        <TradeTimeline data={stats.activityTimeline} />
      </Card>

      {/* Second row */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Policy area breakdown */}
        <Card className="lg:col-span-2" padding="md">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-white">Trades by Policy Area</h2>
              <p className="text-xs text-neutral-500">Blue = total · Red = flagged overlap</p>
            </div>
          </div>
          <PolicyAreaChart data={stats.tradesByPolicyArea} />
        </Card>

        {/* Sector pie */}
        <Card padding="md">
          <div className="mb-3">
            <h2 className="text-sm font-semibold text-white">By Sector</h2>
            <p className="text-xs text-neutral-500">Top traded sectors</p>
          </div>
          <SectorPieChart data={stats.tradesBySector} />
        </Card>
      </div>

      {/* Bottom row: most active + top performers + most traded */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {/* Most active traders */}
        <Card padding="md">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Most Active Traders</h2>
            <Link href="/members" className="text-xs text-brand-400 hover:text-brand-300">All →</Link>
          </div>
          <div className="space-y-2">
            {stats.topTraders.map((trader, i) => (
              <div key={trader.memberId} className="flex items-center gap-2">
                <span className="text-xs text-neutral-600 w-4">{i + 1}</span>
                <Badge className={partyBgClass(trader.party)} size="sm">
                  {partyShort(trader.party)}
                </Badge>
                <Link
                  href={`/members/${trader.memberSlug}`}
                  className="flex-1 truncate text-xs text-white hover:text-brand-400"
                >
                  {trader.memberName}
                </Link>
                <span className="text-xs font-mono text-neutral-400">
                  {trader.tradeCount.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Top estimated performers */}
        <Card padding="md">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Top Performers</h2>
            <div className="flex items-center gap-1">
              <TrendingUp className="h-3.5 w-3.5 text-neutral-500" />
              <Link href="/performers" className="text-xs text-brand-400 hover:text-brand-300">All →</Link>
            </div>
          </div>
          <div className="space-y-2">
            {stats.topPerformers.map((p, i) => (
              <div key={p.memberId} className="flex items-center gap-2">
                <span className="text-xs text-neutral-600 w-4">{i + 1}</span>
                <Link
                  href={`/members/${p.memberSlug}`}
                  className="flex-1 truncate text-xs text-white hover:text-brand-400"
                >
                  {p.memberName}
                </Link>
                <div className="flex items-center gap-1.5">
                  <span className={`text-xs font-mono ${returnColorClass(p.return1y)}`}>
                    {formatReturn(p.return1y)}
                  </span>
                  <Badge className={badgeColorClass(p.badge)} size="sm">
                    {p.badge === "High Outperformance" ? "⚡ High" : p.badge.split(" ")[0]}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Most traded companies */}
        <Card padding="md">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Most Traded Companies</h2>
            <Link href="/companies" className="text-xs text-brand-400 hover:text-brand-300">All →</Link>
          </div>
          <div className="space-y-2">
            {stats.mostTradedCompanies.map((co, i) => (
              <div key={co.ticker} className="flex items-center gap-2">
                <span className="text-xs text-neutral-600 w-4">{i + 1}</span>
                <Link
                  href={`/companies/${co.ticker}`}
                  className="font-mono text-xs text-brand-400 hover:text-brand-300 w-14"
                >
                  {co.ticker}
                </Link>
                <span className="flex-1 truncate text-xs text-neutral-400">{co.companyName}</span>
                <span className="text-xs font-mono text-neutral-400">{co.tradeCount}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
