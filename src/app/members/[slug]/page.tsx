import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ExternalLink, AlertTriangle, TrendingUp } from "lucide-react";
import {
  getMembers,
  getMemberBySlug,
  getTradesByMember,
  getFlagsByMember,
  getPerformanceByMember,
} from "@/lib/data/loader";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { TradeTable } from "@/components/trades/TradeTable";
import { PerformanceChart } from "@/components/charts/PerformanceChart";
import { FlagBadge } from "@/components/trades/FlagBadge";
import {
  partyBgClass,
  partyShort,
  badgeColorClass,
  formatReturn,
  returnColorClass,
  formatCurrency,
  formatDate,
  severityBgClass,
  severityLabel,
} from "@/lib/utils/formatting";
import { buildScoringMethodologyText } from "@/lib/utils/scoring";

export const revalidate = parseInt(process.env.NEXT_REVALIDATE_SECONDS ?? "21600");

export async function generateStaticParams() {
  return getMembers().map((m) => ({ slug: m.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const member = getMemberBySlug(slug);
  if (!member) return { title: "Member Not Found" };
  return {
    title: member.name,
    description: `Congressional trading profile for ${member.name} (${member.party}, ${member.state}).`,
  };
}

export default async function MemberPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const member = getMemberBySlug(slug);
  if (!member) notFound();

  const trades = getTradesByMember(member.id).sort((a, b) =>
    b.disclosureDate.localeCompare(a.disclosureDate)
  );
  const flags = getFlagsByMember(member.id).sort((a, b) => b.overallScore - a.overallScore);
  const perf = getPerformanceByMember(member.id);

  const perfChartData = [
    { label: "1-Year", memberReturn: perf?.estimatedReturn1y, spReturn: perf?.spReturn1y },
    { label: "3-Year", memberReturn: perf?.estimatedReturn3y, spReturn: perf?.spReturn3y },
    { label: "5-Year", memberReturn: perf?.estimatedReturn5y, spReturn: perf?.spReturn5y },
  ].filter((d) => d.memberReturn !== undefined);

  // Sector breakdown from trades
  const sectorMap = new Map<string, number>();
  trades.forEach((t) => {
    sectorMap.set(t.sector, (sectorMap.get(t.sector) ?? 0) + 1);
  });
  const sectors = [...sectorMap.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Hero section */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge className={partyBgClass(member.party)}>
              {member.party} · {partyShort(member.party)}
            </Badge>
            <Badge className="bg-surface border-surface-border text-neutral-400">
              {member.chamber}
            </Badge>
            <Badge className="bg-surface border-surface-border text-neutral-400">
              {member.state}
            </Badge>
          </div>
          <h1 className="text-3xl font-bold text-white">{member.name}</h1>
          {member.officialUrl && (
            <a
              href={member.officialUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 flex items-center gap-1 text-xs text-neutral-500 hover:text-brand-400"
            >
              Official profile <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>

        {perf && (
          <div className="rounded-lg border border-surface-border bg-surface-raised p-4 min-w-52">
            <p className="text-xs text-neutral-500 mb-2">Estimated Performance</p>
            <Badge className={badgeColorClass(perf.badge)}>{perf.badge}</Badge>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center">
              {[
                { label: "1Y", value: perf.estimatedReturn1y },
                { label: "3Y", value: perf.estimatedReturn3y },
                { label: "5Y", value: perf.estimatedReturn5y },
              ].map((r) => (
                <div key={r.label}>
                  <p className="text-xs text-neutral-500">{r.label}</p>
                  <p className={`text-sm font-bold ${returnColorClass(r.value)}`}>
                    {formatReturn(r.value)}
                  </p>
                </div>
              ))}
            </div>
            <p className="mt-2 text-xs text-neutral-600">
              Confidence: {perf.confidence} · Based on {perf.tradeCount} trades
            </p>
          </div>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card padding="sm">
          <p className="text-xs text-neutral-500">Total Trades</p>
          <p className="mt-1 text-xl font-bold text-white">{member.tradeCount}</p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-neutral-500">Flagged Overlaps</p>
          <p className={`mt-1 text-xl font-bold ${member.flaggedTradeCount > 0 ? "text-red-400" : "text-white"}`}>
            {member.flaggedTradeCount}
          </p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-neutral-500">Committees</p>
          <p className="mt-1 text-xl font-bold text-white">{member.committees.length}</p>
        </Card>
        <Card padding="sm">
          <p className="text-xs text-neutral-500">Policy Areas</p>
          <p className="mt-1 text-xl font-bold text-white">{member.policyAreas.length}</p>
        </Card>
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Committees + policy areas */}
        <div className="space-y-4">
          <Card padding="md">
            <h2 className="mb-3 text-sm font-semibold text-white">Committees</h2>
            {member.committees.length === 0 ? (
              <p className="text-xs text-neutral-500">No committee data available.</p>
            ) : (
              <div className="space-y-1.5">
                {member.committees.map((c) => (
                  <div key={c.id} className="flex items-center justify-between">
                    <span className="text-xs text-neutral-300">{c.name}</span>
                    {c.role !== "Member" && (
                      <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30" size="sm">
                        {c.role}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card padding="md">
            <h2 className="mb-3 text-sm font-semibold text-white">Policy Areas</h2>
            <div className="flex flex-wrap gap-1.5">
              {member.policyAreas.map((pa) => (
                <Badge key={pa} className="bg-brand-600/20 text-brand-300 border-brand-500/30" size="sm">
                  {pa}
                </Badge>
              ))}
            </div>
          </Card>

          {sectors.length > 0 && (
            <Card padding="md">
              <h2 className="mb-3 text-sm font-semibold text-white">Sector Concentration</h2>
              <div className="space-y-2">
                {sectors.map(([sector, count]) => {
                  const pct = Math.round((count / trades.length) * 100);
                  return (
                    <div key={sector}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-neutral-300">{sector}</span>
                        <span className="text-neutral-500">{pct}%</span>
                      </div>
                      <div className="h-1.5 rounded bg-surface">
                        <div
                          className="h-full rounded bg-brand-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}
        </div>

        {/* Performance + flags */}
        <div className="space-y-4 lg:col-span-2">
          {/* Performance chart */}
          {perfChartData.length > 0 && (
            <Card padding="md">
              <div className="mb-3 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-neutral-500" />
                <h2 className="text-sm font-semibold text-white">Estimated Portfolio Performance</h2>
              </div>
              <PerformanceChart data={perfChartData} />
              {perf && (
                <div className="mt-3 rounded border border-yellow-500/20 bg-yellow-500/5 p-2">
                  <p className="text-xs text-yellow-300/80">
                    <strong>Note:</strong> {perf.caveats[0] ?? "These are estimates based on disclosed trade timing and reported value ranges. Actual performance may differ significantly."}
                  </p>
                </div>
              )}
            </Card>
          )}

          {/* Top flagged trades */}
          {flags.length > 0 && (
            <Card padding="md">
              <div className="mb-3 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-red-400" />
                <h2 className="text-sm font-semibold text-white">
                  Flagged Overlap Trades ({flags.length})
                </h2>
              </div>
              <div className="space-y-3">
                {flags.slice(0, 5).map((flag) => (
                  <div
                    key={flag.tradeId}
                    className="rounded border border-red-500/20 bg-red-500/5 p-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <Link
                            href={`/companies/${flag.ticker}`}
                            className="font-mono text-sm font-bold text-white hover:text-brand-400"
                          >
                            {flag.ticker}
                          </Link>
                          <span className="text-xs text-neutral-500">{flag.companyName}</span>
                          <Badge className={severityBgClass(flag.severity)} size="sm">
                            {severityLabel(flag.severity)}
                          </Badge>
                        </div>
                        <p className="mt-1 text-xs text-neutral-400">{flag.summary}</p>
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          {flag.matchedPolicyAreas.map((pa) => (
                            <Badge
                              key={pa}
                              className="bg-orange-500/20 text-orange-300 border-orange-500/30"
                              size="sm"
                            >
                              {pa}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="text-lg font-bold text-red-400">{flag.overallScore}</p>
                        <p className="text-xs text-neutral-500">/ 100</p>
                      </div>
                    </div>
                    <div className="mt-2 space-y-1">
                      {flag.factors.slice(0, 3).map((f) => (
                        <div key={f.factor} className="flex items-center gap-2">
                          <span className="w-36 text-xs text-neutral-500 truncate">{f.factor}</span>
                          <div className="flex-1 h-1 rounded bg-surface">
                            <div
                              className="h-full rounded bg-orange-500"
                              style={{ width: `${Math.min(100, (f.score / f.maxScore) * 100)}%` }}
                            />
                          </div>
                          <span className="text-xs text-neutral-500">{f.score}/{f.maxScore}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                {flags.length > 5 && (
                  <Link href={`/flags?memberId=${member.id}`} className="block text-center text-xs text-neutral-500 hover:text-white">
                    View all {flags.length} flagged trades →
                  </Link>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Full trade history */}
      <div>
        <h2 className="mb-3 text-lg font-semibold text-white">
          Full Trade History ({trades.length})
        </h2>
        <TradeTable trades={trades} showMember={false} pageSize={20} />
      </div>
    </div>
  );
}
