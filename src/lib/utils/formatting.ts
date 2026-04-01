import { format, formatDistanceToNow, parseISO } from "date-fns";
import type { AmountRange, Party, FlagSeverity, PerformanceBadge } from "@/lib/types";

// ---- Currency ----------------------------------------------

export function formatAmountRange(range: AmountRange): string {
  return range.label;
}

export function formatAmountMidpoint(range: AmountRange): string {
  const mid = (range.min + range.max) / 2;
  return formatCurrency(mid);
}

export function formatCurrency(n: number): string {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toLocaleString()}`;
}

// ---- Dates -------------------------------------------------

export function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "MMM d, yyyy");
  } catch {
    return dateStr;
  }
}

export function formatDateShort(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "MMM d");
  } catch {
    return dateStr;
  }
}

export function formatDateRelative(dateStr: string): string {
  try {
    return formatDistanceToNow(parseISO(dateStr), { addSuffix: true });
  } catch {
    return dateStr;
  }
}

export function formatMonthYear(dateStr: string): string {
  try {
    return format(parseISO(dateStr), "MMM yyyy");
  } catch {
    return dateStr;
  }
}

// ---- Returns / Percentages ---------------------------------

export function formatReturn(value: number | undefined, decimals = 1): string {
  if (value === undefined || value === null) return "N/A";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}%`;
}

export function returnColorClass(value: number | undefined): string {
  if (value === undefined) return "text-neutral-400";
  if (value >= 5) return "text-gain";
  if (value <= -5) return "text-loss";
  return "text-neutral-300";
}

// ---- Party -------------------------------------------------

export function partyColorClass(party: Party): string {
  switch (party) {
    case "Democrat":    return "text-blue-400";
    case "Republican":  return "text-red-400";
    case "Independent": return "text-purple-400";
    default:            return "text-neutral-400";
  }
}

export function partyBgClass(party: Party): string {
  switch (party) {
    case "Democrat":    return "bg-blue-500/20 text-blue-300 border-blue-500/30";
    case "Republican":  return "bg-red-500/20 text-red-300 border-red-500/30";
    case "Independent": return "bg-purple-500/20 text-purple-300 border-purple-500/30";
    default:            return "bg-neutral-500/20 text-neutral-300 border-neutral-500/30";
  }
}

export function partyShort(party: Party): string {
  switch (party) {
    case "Democrat":    return "D";
    case "Republican":  return "R";
    case "Independent": return "I";
    default:            return "?";
  }
}

// ---- Flag severity -----------------------------------------

export function severityColorClass(severity: FlagSeverity): string {
  switch (severity) {
    case "critical": return "text-red-400";
    case "high":     return "text-orange-400";
    case "medium":   return "text-yellow-400";
    case "low":      return "text-neutral-400";
  }
}

export function severityBgClass(severity: FlagSeverity): string {
  switch (severity) {
    case "critical": return "bg-red-500/20 text-red-300 border-red-500/40";
    case "high":     return "bg-orange-500/20 text-orange-300 border-orange-500/40";
    case "medium":   return "bg-yellow-500/20 text-yellow-300 border-yellow-500/40";
    case "low":      return "bg-neutral-500/20 text-neutral-300 border-neutral-500/40";
  }
}

export function severityLabel(severity: FlagSeverity): string {
  switch (severity) {
    case "critical": return "Critical";
    case "high":     return "High";
    case "medium":   return "Medium";
    case "low":      return "Low";
  }
}

// ---- Performance badge -------------------------------------

export function badgeColorClass(badge: PerformanceBadge): string {
  switch (badge) {
    case "High Outperformance":      return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
    case "Strong Estimated Gains":   return "bg-green-500/20 text-green-300 border-green-500/40";
    case "Watchlist":                return "bg-amber-500/20 text-amber-300 border-amber-500/40";
    case "Market-Tracking":          return "bg-sky-500/20 text-sky-300 border-sky-500/40";
    case "Underperforming":          return "bg-red-500/20 text-red-300 border-red-500/40";
    case "Insufficient Data":        return "bg-neutral-500/20 text-neutral-400 border-neutral-500/40";
  }
}

// ---- Trade type --------------------------------------------

export function tradeTypeColorClass(type: string): string {
  if (type.includes("Purchase")) return "text-gain";
  if (type.includes("Sale"))     return "text-loss";
  return "text-neutral-300";
}

export function tradeTypeBgClass(type: string): string {
  if (type.includes("Purchase")) return "bg-green-500/20 text-green-300 border-green-500/30";
  if (type.includes("Sale"))     return "bg-red-500/20 text-red-300 border-red-500/30";
  return "bg-neutral-500/20 text-neutral-300 border-neutral-500/30";
}

// ---- Misc --------------------------------------------------

export function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return `${str.slice(0, maxLen - 1)}…`;
}

export function capitalize(str: string): string {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
}
