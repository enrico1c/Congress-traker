"use client";

import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import type { DashboardStats } from "@/lib/types";

interface TradeTimelineProps {
  data: DashboardStats["activityTimeline"];
  height?: number;
}

const CustomTooltip = ({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) => {
  if (!active || !payload) return null;
  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised p-3 shadow-xl">
      <p className="mb-2 text-xs font-semibold text-white">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="text-xs" style={{ color: p.color }}>
          {p.name}: {p.value.toLocaleString()}
        </p>
      ))}
    </div>
  );
};

export function TradeTimeline({ data, height = 220 }: TradeTimelineProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" vertical={false} />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 10, fill: "#6b7280" }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 11, color: "#9ca3af" }}
          formatter={(v) => <span style={{ color: "#9ca3af" }}>{v}</span>}
        />
        <Bar dataKey="purchases" name="Purchases" fill="#22c55e" opacity={0.7} radius={[2, 2, 0, 0]} />
        <Bar dataKey="sales"     name="Sales"     fill="#ef4444" opacity={0.7} radius={[2, 2, 0, 0]} />
        <Line
          dataKey="total"
          name="Total"
          type="monotone"
          stroke="#3b82f6"
          strokeWidth={1.5}
          dot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
