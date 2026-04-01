import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Tooltip } from "@/components/ui/Tooltip";
import { severityBgClass, severityLabel } from "@/lib/utils/formatting";
import type { FlagSeverity } from "@/lib/types";

interface FlagBadgeProps {
  severity: FlagSeverity;
  score: number;
  summary?: string;
  tradeId?: string;
  showScore?: boolean;
}

export function FlagBadge({ severity, score, summary, tradeId, showScore = false }: FlagBadgeProps) {
  const badge = (
    <Badge className={severityBgClass(severity)}>
      <AlertTriangle className="mr-1 h-2.5 w-2.5" />
      {showScore ? `${severityLabel(severity)} · ${score}` : severityLabel(severity)}
    </Badge>
  );

  const content = (
    <div className="max-w-60">
      <p className="font-semibold text-white mb-1">
        Policy Overlap: {severityLabel(severity)} ({score}/100)
      </p>
      {summary && <p className="text-neutral-400">{summary}</p>}
      <p className="mt-1 text-neutral-500 text-xs">Click to see full breakdown</p>
    </div>
  );

  const wrapped = <Tooltip content={content}>{badge}</Tooltip>;

  if (tradeId) {
    return (
      <Link href={`/trades/${tradeId}`} className="hover:opacity-80 transition-opacity">
        {wrapped}
      </Link>
    );
  }
  return wrapped;
}
