"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  PieChart, Pie, Cell, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, FunnelChart, Funnel, LabelList,
} from "recharts";
import { motion } from "framer-motion";
import type { ChartSpec, DashboardPage } from "@/lib/types";
import { getData } from "@/lib/api";

interface Props {
  pages: DashboardPage[];
  activePage: number;
  jobId: string;
  colorPalette: string[];
}

const TOOLTIP_STYLE = {
  backgroundColor: "#1E293B",
  border: "1px solid #334155",
  borderRadius: "8px",
  color: "#F8FAFC",
  fontSize: "12px",
};

function ChartCard({ spec, data, colors }: { spec: ChartSpec; data: Record<string, unknown>[]; colors: string[] }) {
  const height = 280;

  const renderChart = () => {
    switch (spec.chart_type) {
      case "bar":
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data.slice(0, 20)} margin={{ top: 5, right: 20, bottom: 20, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey={spec.x_axis || Object.keys(data[0] || {})[0]} tick={{ fill: "#94A3B8", fontSize: 11 }} tickLine={false} />
              <YAxis tick={{ fill: "#94A3B8", fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ color: "#94A3B8", fontSize: 11 }} />
              {spec.data_columns.filter(c => c !== spec.x_axis).slice(0, 3).map((col, i) => (
                <Bar key={col} dataKey={col} fill={colors[i % colors.length]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case "line":
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={data.slice(0, 50)} margin={{ top: 5, right: 20, bottom: 20, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey={spec.x_axis || Object.keys(data[0] || {})[0]} tick={{ fill: "#94A3B8", fontSize: 11 }} tickLine={false} />
              <YAxis tick={{ fill: "#94A3B8", fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ color: "#94A3B8", fontSize: 11 }} />
              {spec.data_columns.filter(c => c !== spec.x_axis).slice(0, 3).map((col, i) => (
                <Line key={col} type="monotone" dataKey={col} stroke={colors[i % colors.length]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case "area":
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={data.slice(0, 50)} margin={{ top: 5, right: 20, bottom: 20, left: 10 }}>
              <defs>
                {spec.data_columns.slice(0, 3).map((col, i) => (
                  <linearGradient key={col} id={`gradient_${i}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={colors[i % colors.length]} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={colors[i % colors.length]} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey={spec.x_axis || Object.keys(data[0] || {})[0]} tick={{ fill: "#94A3B8", fontSize: 11 }} tickLine={false} />
              <YAxis tick={{ fill: "#94A3B8", fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ color: "#94A3B8", fontSize: 11 }} />
              {spec.data_columns.filter(c => c !== spec.x_axis).slice(0, 3).map((col, i) => (
                <Area key={col} type="monotone" dataKey={col} stroke={colors[i % colors.length]} strokeWidth={2}
                  fill={`url(#gradient_${i})`} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );

      case "pie":
      case "donut": {
        const pieKey = spec.y_axis || spec.data_columns[0];
        const labelKey = spec.x_axis || Object.keys(data[0] || {})[0];
        const pieData = data.slice(0, 8).map(d => ({
          name: String(d[labelKey] || ""),
          value: Number(d[pieKey] || 0),
        }));
        const inner = spec.chart_type === "donut" ? "55%" : "0%";
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius="75%" innerRadius={inner}
                dataKey="value" label={({ name, percent }: { name?: string; percent?: number }) => `${name ?? ""}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                labelLine={{ stroke: "#475569" }}
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={colors[i % colors.length]} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ color: "#94A3B8", fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        );
      }

      case "scatter":
        return (
          <ResponsiveContainer width="100%" height={height}>
            <ScatterChart margin={{ top: 5, right: 20, bottom: 20, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey={spec.x_axis || spec.data_columns[0]} name={spec.x_axis} tick={{ fill: "#94A3B8", fontSize: 11 }} tickLine={false} />
              <YAxis dataKey={spec.y_axis || spec.data_columns[1]} name={spec.y_axis} tick={{ fill: "#94A3B8", fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ strokeDasharray: "3 3" }} />
              <Scatter data={data.slice(0, 200)} fill={colors[0]} fillOpacity={0.7} />
            </ScatterChart>
          </ResponsiveContainer>
        );

      default:
        return (
          <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
            {spec.chart_type} chart
          </div>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="chart-container"
    >
      <h3 className="font-semibold text-sm text-white mb-1">{spec.title}</h3>
      {spec.subtitle && <p className="text-xs text-slate-500 mb-3">{spec.subtitle}</p>}
      {data.length > 0 ? renderChart() : (
        <div className="flex items-center justify-center h-48">
          <div className="shimmer w-full h-full rounded-lg" />
        </div>
      )}
    </motion.div>
  );
}

export default function ChartGrid({ pages, activePage, jobId, colorPalette }: Props) {
  const [chartData, setChartData] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    if (!jobId) return;
    getData(jobId, 1, 500).then((d) => setChartData(d.data || [])).catch(() => {});
  }, [jobId]);

  const page = pages.find((p) => p.page_number === activePage);
  if (!page) return null;

  const colors = colorPalette.length >= 4
    ? colorPalette.slice(1)
    : ["#6366F1", "#22D3EE", "#10B981", "#F59E0B", "#EF4444", "#A855F7"];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {page.charts.map((chart) => (
        <div
          key={chart.chart_id}
          className={
            chart.position?.width >= 6
              ? "md:col-span-2 xl:col-span-3"
              : chart.position?.width >= 4
              ? "md:col-span-2"
              : ""
          }
        >
          <ChartCard spec={chart} data={chartData} colors={colors} />
        </div>
      ))}
    </div>
  );
}
