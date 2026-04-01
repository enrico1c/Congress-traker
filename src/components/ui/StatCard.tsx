import { clsx } from "clsx";
import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  subvalue?: string;
  icon?: ReactNode;
  trend?: "up" | "down" | "neutral";
  trendLabel?: string;
  className?: string;
}

export function StatCard({
  label,
  value,
  subvalue,
  icon,
  trend,
  trendLabel,
  className,
}: StatCardProps) {
  const trendColor = { up: "text-gain", down: "text-loss", neutral: "text-neutral-400" }[
    trend ?? "neutral"
  ];

  return (
    <div
      className={clsx(
        "rounded-lg border border-surface-border bg-surface-raised p-4",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide">{label}</p>
        {icon && <div className="text-neutral-500">{icon}</div>}
      </div>
      <p className="mt-2 text-2xl font-bold text-white tabular-nums">{value}</p>
      {(subvalue || trendLabel) && (
        <p className={clsx("mt-1 text-xs", trendLabel ? trendColor : "text-neutral-500")}>
          {trendLabel || subvalue}
        </p>
      )}
    </div>
  );
}
