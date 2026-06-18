import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChartType, ColumnMeta } from "@/features/named-queries/api/contracts";

type Props = {
  chartType: ChartType;
  columns: ColumnMeta[];
  rows: Record<string, unknown>[];
};

export function NamedQueryChart({ chartType, columns, rows }: Props) {
  if (columns.length < 2 || rows.length === 0) return null;

  const xKey = columns[0].name;
  const dataKeys = columns.slice(1).map((c) => c.name);
  const data = rows.map((row) => {
    const point: Record<string, unknown> = { [xKey]: row[xKey] };
    dataKeys.forEach((k) => {
      const v = row[k];
      point[k] = v != null ? Number(v) : null;
    });
    return point;
  });

  const colors = ["var(--brand-500)", "var(--success-700)", "var(--danger-700)"];

  if (chartType === "bar") {
    return (
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
          <XAxis dataKey={xKey} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          {dataKeys.map((key, i) => (
            <Bar key={key} dataKey={key} fill={colors[i % colors.length]} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
        <XAxis dataKey={xKey} tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        {dataKeys.map((key, i) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={colors[i % colors.length]}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
