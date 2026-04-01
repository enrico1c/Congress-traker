/**
 * /api/live — Proxies Senate EFTS for real-time disclosure data.
 * Senate EFTS is a public JSON API, no key required, updated frequently.
 * This route is never cached so the client always gets fresh data.
 */
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SENATE_EFTS = "https://efts.senate.gov/LATEST/search-index";
const DAYS_BACK = 60; // how far back to look for recent disclosures

interface EftsHit {
  _id: string;
  _source: {
    senator_name?: string;
    first_name?: string;
    last_name?: string;
    ticker?: string;
    asset_name?: string;
    type?: string;
    transaction_date?: string;
    disclosure_date?: string;
    date?: string;
    amount?: string;
    comment?: string;
    state?: string;
    party?: string;
  };
}

export interface LiveTrade {
  id: string;
  memberName: string;
  party: string;
  state: string;
  ticker: string;
  assetName: string;
  tradeType: string;
  tradeDate: string;
  disclosureDate: string;
  amount: string;
  chamber: "Senate";
}

export interface LiveResponse {
  trades: LiveTrade[];
  total: number;
  fetchedAt: string;
  source: string;
}

function fromDate(): string {
  const d = new Date(Date.now() - DAYS_BACK * 24 * 60 * 60 * 1000);
  return d.toISOString().split("T")[0];
}

export async function GET() {
  try {
    const params = new URLSearchParams({
      q: "",
      dateRange: "custom",
      fromDate: fromDate(),
      toDate: new Date().toISOString().split("T")[0],
      pageSize: "30",
      offset: "0",
    });

    const res = await fetch(`${SENATE_EFTS}?${params}`, {
      headers: {
        "User-Agent": "CongressTrades/1.0 (public transparency tool)",
        Accept: "application/json",
      },
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: `Senate EFTS returned ${res.status}` },
        { status: 502 }
      );
    }

    const data = await res.json();
    const hits: EftsHit[] = data.hits?.hits ?? [];

    const trades: LiveTrade[] = hits.map((hit) => {
      const s = hit._source;
      const name =
        s.senator_name ??
        [s.first_name, s.last_name].filter(Boolean).join(" ") ??
        "Unknown";
      return {
        id: hit._id,
        memberName: name,
        party: s.party ?? "",
        state: s.state ?? "",
        ticker: s.ticker ?? "",
        assetName: s.asset_name ?? "",
        tradeType: s.type ?? "",
        tradeDate: s.transaction_date ?? s.date ?? "",
        disclosureDate: s.disclosure_date ?? s.date ?? "",
        amount: s.amount ?? "",
        chamber: "Senate",
      };
    });

    const response: LiveResponse = {
      trades,
      total: data.hits?.total?.value ?? trades.length,
      fetchedAt: new Date().toISOString(),
      source: "Senate EFTS (efts.senate.gov)",
    };

    return NextResponse.json(response, {
      headers: {
        "Cache-Control": "no-store",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (err) {
    return NextResponse.json(
      { error: "Failed to fetch live data", detail: String(err) },
      { status: 500 }
    );
  }
}
