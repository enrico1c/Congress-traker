"use client";

import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";

interface SectorPieChartProps {
  data: Array<{ sector: string; count: number }>;
  height?: number;
}

const COLORS = [
  "#3b82f6","#22c55e","#f59e0b","#ef4444","#8b5cf6",
  "#06b6d4","#f97316","#ec4899","#14b8a6","#84cc16","#a78bfa","#fb7185",
];

const CustomTooltip = ({ active, payload }: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; payload: { sector: string } }>;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised p-2 shadow-xl">
      <p className="text-xs font-semibold text-white">{payload[0].payload.sector}</p>
      <p className="text-xs text-neutral-400">{payload[0].value.toLocaleString()} trades</p>
    </div>
  );
};

export function SectorPieChart({ data, height = 260 }: SectorPieChartProps) {
  const sorted = [...data].sort((a, b) => b.count - a.count).slice(0, 10);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={sorted}
          dataKey="count"
          nameKey="sector"
          cx="50%"
          cy="50%"
          outerRadius={80}
          innerRadius={40}
          paddingAngle={2}
        >
          {sorted.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} opacity={0.85} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          formatter={(v) => <span style={{ color: "#9ca3af", fontSize: 10 }}>{v}</span>}
          iconSize={8}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
