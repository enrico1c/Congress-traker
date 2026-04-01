"use client";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Cell,
} from "recharts";

interface PerformanceChartProps {
  data: Array<{
    label: string;
    memberReturn?: number;
    spReturn?: number;
  }>;
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
          {p.name}: {p.value != null ? `${p.value > 0 ? "+" : ""}${p.value.toFixed(1)}%` : "N/A"}
        </p>
      ))}
    </div>
  );
};

export function PerformanceChart({ data, height = 200 }: PerformanceChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }} barGap={2}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#6b7280" }} tickLine={false} axisLine={false} />
        <YAxis
          tick={{ fontSize: 10, fill: "#6b7280" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${v}%`}
        />
        <ReferenceLine y={0} stroke="#2d3748" />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="memberReturn" name="Est. Return" radius={[3, 3, 0, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={(entry.memberReturn ?? 0) >= 0 ? "#22c55e" : "#ef4444"}
              opacity={0.8}
            />
          ))}
        </Bar>
        <Bar dataKey="spReturn" name="S&P 500" fill="#374151" opacity={0.7} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
