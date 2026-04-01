/**
 * Client-side scoring utilities for display purposes.
 * The authoritative score is computed by the Python pipeline (engines/overlap_scorer.py).
 * These functions recreate the display logic transparently.
 */
import type { Trade, Member, Company, FlagFactor, FlagSeverity } from "@/lib/types";

export const SCORE_THRESHOLDS = {
  critical: 75,
  high: 50,
  medium: 25,
  low: 0,
} as const;

export function scoreToSeverity(score: number): FlagSeverity {
  if (score >= SCORE_THRESHOLDS.critical) return "critical";
  if (score >= SCORE_THRESHOLDS.high)     return "high";
  if (score >= SCORE_THRESHOLDS.medium)   return "medium";
  return "low";
}

export const SCORING_FACTORS = {
  COMMITTEE_JURISDICTION_MATCH: {
    name: "Committee jurisdiction match",
    max: 35,
    description: "The member serves on a committee with direct jurisdiction over this industry.",
  },
  POLICY_AREA_MATCH: {
    name: "Policy area match",
    max: 25,
    description: "The member is tagged to a policy area that overlaps with the company's sector.",
  },
  SECTOR_CONCENTRATION: {
    name: "Sector concentration",
    max: 15,
    description: "This member has made multiple trades in this sector, suggesting focused interest.",
  },
  TRADE_SIZE: {
    name: "Estimated trade size",
    max: 10,
    description: "Larger reported trade amounts increase relevance.",
  },
  RECENCY: {
    name: "Trade recency",
    max: 10,
    description: "More recent trades near key legislative events are weighted higher.",
  },
  DISCLOSURE_DELAY: {
    name: "Late disclosure",
    max: 5,
    description: "Trades disclosed significantly after the 45-day STOCK Act window may indicate oversight issues.",
  },
} as const;

export type ScoringFactorKey = keyof typeof SCORING_FACTORS;

export function buildScoringMethodologyText(): string {
  const factors = Object.values(SCORING_FACTORS);
  const total = factors.reduce((sum, f) => sum + f.max, 0);
  const lines = factors.map(
    (f) => `• **${f.name}** (max ${f.max} pts): ${f.description}`
  );
  return [
    `Trades are scored on a 0–${total} scale across ${factors.length} factors:`,
    "",
    ...lines,
    "",
    "Scores ≥75 = Critical · ≥50 = High · ≥25 = Medium · <25 = Low",
    "",
    "**Important**: A high score is an informational signal, not evidence of wrongdoing. " +
      "Many high-scoring trades are legal and routine. This tool exists to support public " +
      "transparency, not to make legal conclusions.",
  ].join("\n");
}

/**
 * Calculate percentage of max score for progress bar display.
 */
export function factorPercent(factor: FlagFactor): number {
  return Math.min(100, Math.round((factor.score / factor.maxScore) * 100));
}
