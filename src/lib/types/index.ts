// ============================================================
// Core domain types for Congress Trades
// ============================================================

// ---- Enumerations ------------------------------------------

export type Chamber = "House" | "Senate";
export type Party = "Democrat" | "Republican" | "Independent" | "Other";
export type TradeType = "Purchase" | "Sale" | "Sale (Partial)" | "Exchange";
export type FlagSeverity = "critical" | "high" | "medium" | "low";
export type PerformanceBadge =
  | "High Outperformance"
  | "Strong Estimated Gains"
  | "Watchlist"
  | "Market-Tracking"
  | "Underperforming"
  | "Insufficient Data";

export const POLICY_AREAS = [
  "Defense",
  "Healthcare",
  "Energy",
  "Technology",
  "Banking / Financial Services",
  "Transportation",
  "Agriculture",
  "Real Estate / Housing",
  "Education",
  "Pharmaceuticals",
  "Telecom / Media",
  "Industrial / Manufacturing",
  "Consumer / Retail",
  "Environment / Climate",
  "Judiciary / Regulation",
] as const;

export type PolicyArea = (typeof POLICY_AREAS)[number];

// ---- Amount ranges (STOCK Act uses ranges, not exact values) ---

export interface AmountRange {
  min: number;   // USD
  max: number;   // USD
  label: string; // e.g. "$1,001 - $15,000"
}

// ---- Member ------------------------------------------------

export interface CommitteeRef {
  id: string;
  name: string;
  role: "Member" | "Chair" | "Ranking Member" | "Vice Chair";
}

export interface Member {
  id: string;             // e.g. "N000032"  (bioguide ID)
  slug: string;           // URL-safe e.g. "pelosi-nancy"
  name: string;
  firstName: string;
  lastName: string;
  party: Party;
  chamber: Chamber;
  state: string;          // Two-letter abbreviation
  district?: string;      // House only
  photoUrl?: string;
  officialUrl?: string;
  committees: CommitteeRef[];
  policyAreas: PolicyArea[];
  tradeCount: number;
  flaggedTradeCount: number;
  totalValueMin: number;
  totalValueMax: number;
  performanceBadge: PerformanceBadge;
  estimatedReturn1y?: number;
  estimatedReturn3y?: number;
  estimatedReturn5y?: number;
  performanceConfidence: "high" | "medium" | "low";
  lastDisclosureDate?: string; // ISO date
  isActive: boolean;
}

// ---- Committee ---------------------------------------------

export interface Committee {
  id: string;
  name: string;
  chamber: Chamber;
  policyAreas: PolicyArea[];
  memberIds: string[];
}

// ---- Company -----------------------------------------------

export interface Company {
  ticker: string;
  name: string;
  sector: string;
  industry: string;
  policyAreas: PolicyArea[];  // Mapped from sector/industry
  marketCap?: number;
  tradeCount: number;
  flaggedTradeCount: number;
  uniqueTraders: number;
  latestTradeDate?: string;
  buyCount: number;
  sellCount: number;
}

// ---- Trade -------------------------------------------------

export interface Trade {
  id: string;
  memberId: string;
  memberName: string;
  memberSlug: string;
  memberParty: Party;
  memberChamber: Chamber;
  memberState: string;
  ticker: string;
  companyName: string;
  sector: string;
  industry: string;
  tradeType: TradeType;
  tradeDate: string;        // ISO date (may be approximate — see dateApproximate)
  dateApproximate: boolean;
  disclosureDate: string;   // ISO date
  disclosureDelay: number;  // days between trade and disclosure
  amount: AmountRange;
  assetType: string;        // "Stock", "Option", "Bond", etc.
  comment?: string;
  sourceUrl: string;
  isFlagged: boolean;
  flagScore?: number;
  flagSeverity?: FlagSeverity;
}

// ---- Trade Flag --------------------------------------------

export interface FlagFactor {
  factor: string;
  score: number;
  maxScore: number;
  explanation: string;
}

export interface TradeFlag {
  tradeId: string;
  memberId: string;
  memberName: string;
  memberSlug: string;
  ticker: string;
  companyName: string;
  tradeDate: string;
  tradeType: TradeType;
  amount: AmountRange;
  overallScore: number;       // 0–100
  severity: FlagSeverity;
  matchedPolicyAreas: PolicyArea[];
  matchedCommittees: CommitteeRef[];
  companySector: string;
  companyIndustry: string;
  factors: FlagFactor[];
  summary: string;            // Human-readable one-liner
}

// ---- Performance snapshot ----------------------------------

export interface PerformanceSnapshot {
  memberId: string;
  memberName: string;
  memberSlug: string;
  estimatedReturn1y?: number;
  estimatedReturn3y?: number;
  estimatedReturn5y?: number;
  spReturn1y?: number;        // S&P 500 benchmark
  spReturn3y?: number;
  spReturn5y?: number;
  excessReturn1y?: number;    // vs S&P
  excessReturn3y?: number;
  excessReturn5y?: number;
  confidence: "high" | "medium" | "low";
  badge: PerformanceBadge;
  tradeCount: number;
  methodology: string;
  caveats: string[];
}

// ---- Dashboard aggregates ----------------------------------

export interface DashboardStats {
  totalMembers: number;
  totalTrades: number;
  totalFlaggedTrades: number;
  totalCompanies: number;
  lastUpdated: string;
  recentTrades: Trade[];
  topTraders: Array<{ memberId: string; memberName: string; memberSlug: string; tradeCount: number; party: Party }>;
  topPerformers: Array<{ memberId: string; memberName: string; memberSlug: string; badge: PerformanceBadge; return1y?: number }>;
  mostTradedCompanies: Array<{ ticker: string; companyName: string; tradeCount: number; sector: string }>;
  tradesByPolicyArea: Array<{ policyArea: PolicyArea; tradeCount: number; flaggedCount: number }>;
  activityTimeline: Array<{ month: string; purchases: number; sales: number; total: number }>;
  tradesBySector: Array<{ sector: string; count: number; flaggedCount: number }>;
}

// ---- Filter state ------------------------------------------

export interface TradeFilters {
  memberId?: string;
  ticker?: string;
  chamber?: Chamber;
  party?: Party;
  state?: string;
  policyArea?: PolicyArea;
  committee?: string;
  sector?: string;
  tradeType?: TradeType;
  dateFrom?: string;
  dateTo?: string;
  flaggedOnly?: boolean;
  query?: string;
}

export interface MemberFilters {
  chamber?: Chamber;
  party?: Party;
  state?: string;
  policyArea?: PolicyArea;
  topPerformersOnly?: boolean;
  query?: string;
}

// ---- Data source manifest ----------------------------------

export interface DataSourceStatus {
  name: string;
  url: string;
  requiresKey: boolean;
  keyName?: string;
  lastFetched?: string;
  recordCount?: number;
  healthy: boolean;
  notes: string;
}

export interface DataManifest {
  generatedAt: string;
  sources: DataSourceStatus[];
  pipelineVersion: string;
}
