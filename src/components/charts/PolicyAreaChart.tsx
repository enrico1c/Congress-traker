"use client";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from "recharts";
import type { DashboardStats } from "@/lib/types";

interface PolicyAreaChartProps {
  data: DashboardStats["tradesByPolicyArea"];
  height?: number;
}

const CustomTooltip = ({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ name: string; value: number }>;
  label?: string;
}) => {
  if (!active || !payload) return null;
  const total = payload.find((p) => p.name === "trades")?.value ?? 0;
  const flagged = payload.find((p) => p.name === "flagged")?.value ?? 0;
  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised p-3 shadow-xl">
      <p className="mb-2 text-xs font-semibold text-white">{label}</p>
      <p className="text-xs text-neutral-300">{total.toLocaleString()} trades</p>
      <p className="text-xs text-red-400">{flagged.toLocaleString()} flagged</p>
    </div>
  );
};

export function PolicyAreaChart({ data, height = 300 }: PolicyAreaChartProps) {
  // Sort by total trade count descending
  const sorted = [...data].sort((a, b) => b.tradeCount - a.tradeCount).slice(0, 12);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={sorted}
        layout="vertical"
        margin={{ top: 0, right: 32, left: 0, bottom: 0 }}
        barSize={10}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} />
        <YAxis
          dataKey="policyArea"
          type="category"
          width={160}
          tick={{ fontSize: 10, fill: "#9ca3af" }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="tradeCount" name="trades" fill="#3b82f6" opacity={0.7} radius={[0, 3, 3, 0]}>
          {sorted.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.flaggedCount > 0 ? "#3b82f6" : "#374151"}
            />
          ))}
        </Bar>
        <Bar dataKey="flaggedCount" name="flagged" fill="#ef4444" opacity={0.85} radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
