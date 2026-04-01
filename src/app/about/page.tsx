import type { Metadata } from "next";
import { Card } from "@/components/ui/Card";
import { getDataManifest } from "@/lib/data/loader";
import { formatDate } from "@/lib/utils/formatting";
import { CheckCircle, XCircle, AlertCircle } from "lucide-react";

export const metadata: Metadata = {
  title: "Methodology & Sources",
  description: "How CongressTrades works: data sources, scoring methodology, and limitations.",
};

export const revalidate = parseInt(process.env.NEXT_REVALIDATE_SECONDS ?? "21600");

export default function AboutPage() {
  const manifest = getDataManifest();

  return (
    <div className="mx-auto max-w-3xl space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-white">Methodology & Data Sources</h1>
        <p className="mt-2 text-neutral-500">
          Transparency about how CongressTrades works, its limitations, and where data comes from.
        </p>
      </div>

      {/* What this is */}
      <Card padding="lg">
        <h2 className="mb-4 text-lg font-semibold text-white">What This Tool Is</h2>
        <div className="space-y-3 text-sm text-neutral-400 leading-relaxed">
          <p>
            CongressTrades is a public-information transparency tool. It aggregates, normalizes, and
            presents U.S. congressional stock trade disclosures filed under the{" "}
            <strong className="text-white">STOCK Act (Stop Trading on Congressional Knowledge Act)</strong>,
            passed in 2012.
          </p>
          <p>
            The STOCK Act requires members of Congress, their spouses, and dependent children to
            disclose stock trades within 45 days. Trades above $1,000 must be reported. The disclosures
            are available as public records from the House and Senate.
          </p>
          <p>
            This tool does <strong className="text-red-400">not</strong> prove or allege insider trading
            or any wrongdoing. It is an organizational and research tool for journalists, researchers,
            and the public.
          </p>
        </div>
      </Card>

      {/* Data sources */}
      <Card padding="lg" id="sources">
        <h2 className="mb-4 text-lg font-semibold text-white">Data Sources</h2>
        <div className="space-y-4">
          {[
            {
              name: "House Periodic Transaction Reports",
              url: "https://disclosures.house.gov/",
              key: false,
              description: "Official ZIP archives of House member trade disclosures, updated periodically. No API key required. Covers 2012–present.",
            },
            {
              name: "Senate EFTS (Electronic Filing & Tracking System)",
              url: "https://efts.senate.gov/LATEST/search-index",
              key: false,
              description: "JSON REST API for Senate financial disclosures. No API key required. Returns structured trade data paginated by date.",
            },
            {
              name: "unitedstates/congress (GitHub)",
              url: "https://github.com/unitedstates/congress",
              key: false,
              description: "Public domain data on members, committees, and legislative history. Updated by a community of civic hackers.",
            },
            {
              name: "Yahoo Finance (via yfinance)",
              url: "https://finance.yahoo.com",
              key: false,
              description: "Historical and current price data, company sector/industry classification. Used for performance estimation. Unofficial but reliable.",
            },
            {
              name: "SEC EDGAR Company Search",
              url: "https://efts.sec.gov/LATEST/search-index",
              key: false,
              description: "Used to resolve company names and CIK numbers for ticker disambiguation. Official SEC data, no key required.",
            },
          ].map((src) => (
            <div key={src.name} className="flex gap-3">
              {src.key ? (
                <AlertCircle className="h-4 w-4 flex-shrink-0 text-yellow-400 mt-0.5" />
              ) : (
                <CheckCircle className="h-4 w-4 flex-shrink-0 text-gain mt-0.5" />
              )}
              <div>
                <div className="flex items-center gap-2">
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-white hover:text-brand-400"
                  >
                    {src.name} ↗
                  </a>
                  {src.key ? (
                    <span className="text-xs text-yellow-400">Free key required</span>
                  ) : (
                    <span className="text-xs text-gain">No key required</span>
                  )}
                </div>
                <p className="text-xs text-neutral-500 mt-0.5">{src.description}</p>
              </div>
            </div>
          ))}
        </div>

        {manifest && (
          <div className="mt-6 rounded border border-surface-border bg-surface p-3">
            <p className="text-xs text-neutral-500">
              Pipeline last run: {formatDate(manifest.generatedAt)} · Version {manifest.pipelineVersion}
            </p>
          </div>
        )}
      </Card>

      {/* Scoring methodology */}
      <Card padding="lg" id="scoring">
        <h2 className="mb-4 text-lg font-semibold text-white">Policy Overlap Scoring</h2>
        <p className="mb-4 text-sm text-neutral-400">
          Each flagged trade receives a score from 0–100 across six factors. Higher scores indicate
          stronger overlap between the member's role and the company traded — not that wrongdoing occurred.
        </p>
        <div className="space-y-3">
          {[
            { factor: "Committee Jurisdiction Match", max: 35, description: "The member serves on a committee with direct legislative oversight of this company's industry. This is the strongest indicator of potential conflict of interest." },
            { factor: "Policy Area Match",            max: 25, description: "The member is tagged to a policy area (e.g. Defense, Healthcare) that aligns with the company's sector. Derived from committee assignments and legislative focus." },
            { factor: "Sector Concentration",         max: 15, description: "The member has made multiple trades in this same sector, suggesting focused interest. Calculated as a proportion of the member's total trades in related sectors." },
            { factor: "Trade Size",                   max: 10, description: "Larger reported amounts (using value range midpoints) score higher. Trades in the $1M+ range score maximum." },
            { factor: "Recency",                      max: 10, description: "Trades are weighted by recency. More recent disclosures score higher." },
            { factor: "Late Disclosure",              max: 5,  description: "Trades disclosed more than 45 days after the transaction (the legal STOCK Act window) are flagged. Very late disclosures (90+ days) score the maximum." },
          ].map((row) => (
            <div key={row.factor} className="flex items-start gap-3">
              <div className="flex-shrink-0 w-16 text-right">
                <span className="text-sm font-bold text-white">{row.max}</span>
                <span className="text-xs text-neutral-500"> pts</span>
              </div>
              <div>
                <p className="text-sm font-medium text-white">{row.factor}</p>
                <p className="text-xs text-neutral-500 mt-0.5">{row.description}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 rounded border border-surface-border bg-surface p-3 text-xs text-neutral-500">
          <strong className="text-neutral-300">Severity levels:</strong> Critical ≥75 · High ≥50 · Medium ≥25 · Low &lt;25
        </div>
      </Card>

      {/* Performance methodology */}
      <Card padding="lg" id="performance">
        <h2 className="mb-4 text-lg font-semibold text-white">Performance Estimation Methodology</h2>
        <div className="space-y-3 text-sm text-neutral-400 leading-relaxed">
          <p>Estimated portfolio returns are calculated using the following simplified model:</p>
          <ol className="list-decimal list-inside space-y-2 ml-2">
            <li>Extract all disclosed purchase and sale transactions for a member</li>
            <li>Use the <strong className="text-white">midpoint of the reported value range</strong> as the trade amount</li>
            <li>Fetch historical prices from Yahoo Finance for each ticker on the trade date</li>
            <li>Model each purchase as a position opened at the trade date price</li>
            <li>Model each sale as a position closed at the trade date price</li>
            <li>Calculate a weighted average return across all positions in the period</li>
            <li>Compare against S&P 500 (SPY) as a benchmark</li>
          </ol>
          <div className="rounded border border-red-500/20 bg-red-500/5 p-3">
            <p className="text-xs text-red-300/80">
              <strong>Important limitations:</strong> (1) We only see disclosed transactions, not the full portfolio.
              (2) Trades are disclosed up to 45 days late, so timing is imprecise.
              (3) Value ranges may span an order of magnitude (e.g. $50K–$100K).
              (4) Undisclosed trades, dividends, and portfolio changes are not captured.
              Treat all performance figures as illustrative estimates with high uncertainty.
            </p>
          </div>
        </div>
      </Card>

      {/* Limitations */}
      <Card padding="lg">
        <h2 className="mb-4 text-lg font-semibold text-white">Known Limitations</h2>
        <div className="space-y-2 text-sm text-neutral-400">
          {[
            "Disclosures can be filed up to 45 days after the trade; high-frequency traders may appear less active than they are",
            "The STOCK Act requires disclosure of trades over $1,000; very small trades are not captured",
            "Some members file amended disclosures; our pipeline uses the most recent filing but may not always capture amendments",
            "Spousal and dependent trades are included in disclosures but not always attributed separately",
            "Not all members comply reliably; enforcement is inconsistent and fines are rare",
            "Company name → ticker resolution is automated and may occasionally produce mismatches",
            "Sector and policy area mappings are heuristic and may not reflect all nuances of legislative jurisdiction",
          ].map((limitation, i) => (
            <div key={i} className="flex gap-2">
              <span className="text-neutral-600 flex-shrink-0">•</span>
              <span>{limitation}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
