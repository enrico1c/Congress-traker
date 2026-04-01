/**
 * Data artifact loader — reads pre-processed JSON files from /data/artifacts/.
 * All data is loaded server-side (Next.js App Router server components).
 * No API calls are made from this module; everything is pre-computed by the pipeline.
 */
import fs from "fs";
import path from "path";
import type {
  Member,
  Committee,
  Company,
  Trade,
  TradeFlag,
  PerformanceSnapshot,
  DashboardStats,
  DataManifest,
} from "@/lib/types";

const ARTIFACTS_DIR = path.join(process.cwd(), "data", "artifacts");

function readArtifact<T>(filename: string): T {
  const filePath = path.join(ARTIFACTS_DIR, filename);
  if (!fs.existsSync(filePath)) {
    console.warn(`[loader] Artifact not found: ${filename}. Returning empty fallback.`);
    // Return typed empty fallback — prevents hard crashes during development
    return (Array.isArray([] as unknown as T) ? [] : {}) as T;
  }
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as T;
}

// ---- Members -----------------------------------------------

let _members: Member[] | null = null;
export function getMembers(): Member[] {
  if (!_members) _members = readArtifact<Member[]>("members.json");
  return _members;
}

export function getMemberById(id: string): Member | undefined {
  return getMembers().find((m) => m.id === id);
}

export function getMemberBySlug(slug: string): Member | undefined {
  return getMembers().find((m) => m.slug === slug);
}

// ---- Committees --------------------------------------------

let _committees: Committee[] | null = null;
export function getCommittees(): Committee[] {
  if (!_committees) _committees = readArtifact<Committee[]>("committees.json");
  return _committees;
}

// ---- Companies ---------------------------------------------

let _companies: Company[] | null = null;
export function getCompanies(): Company[] {
  if (!_companies) _companies = readArtifact<Company[]>("companies.json");
  return _companies;
}

export function getCompanyByTicker(ticker: string): Company | undefined {
  return getCompanies().find((c) => c.ticker === ticker.toUpperCase());
}

// ---- Trades ------------------------------------------------

let _trades: Trade[] | null = null;
export function getTrades(): Trade[] {
  if (!_trades) _trades = readArtifact<Trade[]>("trades.json");
  return _trades;
}

export function getTradesByMember(memberId: string): Trade[] {
  return getTrades().filter((t) => t.memberId === memberId);
}

export function getTradesByTicker(ticker: string): Trade[] {
  return getTrades().filter((t) => t.ticker === ticker.toUpperCase());
}

export function getRecentTrades(n = 50): Trade[] {
  return getTrades()
    .sort((a, b) => b.disclosureDate.localeCompare(a.disclosureDate))
    .slice(0, n);
}

// ---- Flags -------------------------------------------------

let _flags: TradeFlag[] | null = null;
export function getFlags(): TradeFlag[] {
  if (!_flags) _flags = readArtifact<TradeFlag[]>("flags.json");
  return _flags;
}

export function getFlagByTradeId(tradeId: string): TradeFlag | undefined {
  return getFlags().find((f) => f.tradeId === tradeId);
}

export function getFlagsByMember(memberId: string): TradeFlag[] {
  return getFlags().filter((f) => f.memberId === memberId);
}

// ---- Performance -------------------------------------------

let _performance: PerformanceSnapshot[] | null = null;
export function getPerformanceSnapshots(): PerformanceSnapshot[] {
  if (!_performance)
    _performance = readArtifact<PerformanceSnapshot[]>("performance.json");
  return _performance;
}

export function getPerformanceByMember(memberId: string): PerformanceSnapshot | undefined {
  return getPerformanceSnapshots().find((p) => p.memberId === memberId);
}

// ---- Dashboard ---------------------------------------------

let _dashboard: DashboardStats | null = null;
export function getDashboardStats(): DashboardStats {
  if (!_dashboard) _dashboard = readArtifact<DashboardStats>("dashboard.json");
  return _dashboard;
}

// ---- Manifest ----------------------------------------------

export function getDataManifest(): DataManifest | null {
  try {
    return readArtifact<DataManifest>("manifest.json");
  } catch {
    return null;
  }
}
