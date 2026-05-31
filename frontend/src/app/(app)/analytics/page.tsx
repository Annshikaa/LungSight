"use client";

import { useEffect, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, CartesianGrid, Cell,
  Legend, PieChart, Pie, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Header } from "@/components/layout/Header";
import { getAnalytics, type AnalyticsResponse } from "@/lib/api";
import { formatPercent, formatNumber } from "@/lib/utils";

const SEV_COLORS = { Normal:"#22c55e", Mild:"#84cc16", Moderate:"#f59e0b", Severe:"#ef4444", Critical:"#7f1d1d" };
const MODEL_COLORS = ["#0ea5e9","#8b5cf6","#22c55e","#f59e0b","#ec4899"];

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);

  useEffect(() => { getAnalytics().then(setData).catch(console.error); }, []);

  if (!data) return (
    <div className="flex h-full items-center justify-center">
      <div className="h-10 w-10 rounded-full border-4 border-medical-200 border-t-medical-500 animate-spin" />
    </div>
  );

  const sevData = Object.entries(data.severity_distribution).map(([k, v]) => ({ name: k, value: v, color: SEV_COLORS[k as keyof typeof SEV_COLORS] }));
  const modelData = Object.entries(data.model_usage).map(([model, count], i) => ({ model, count, fill: MODEL_COLORS[i] }));

  return (
    <div className="flex flex-col min-h-full">
      <Header title="Analytics" />
      <div className="flex-1 p-6 space-y-6">

        {/* KPI */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Total Scans",        value: formatNumber(data.total_scans) },
            { label: "Avg Confidence",     value: formatPercent(data.average_confidence * 100) },
            { label: "Avg Severity Score", value: `${data.average_severity_score.toFixed(1)}/100` },
            { label: "Est. Model Accuracy",value: formatPercent(data.model_accuracy_estimate * 100) },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-2xl border border-border bg-card p-5">
              <div className="text-xs text-muted-foreground mb-1">{label}</div>
              <div className="text-3xl font-extrabold text-foreground">{value}</div>
            </div>
          ))}
        </div>

        {/* Trend */}
        <div className="rounded-2xl border border-border bg-card p-5">
          <h3 className="text-sm font-bold text-foreground mb-4">30-Day Prediction Volume</h3>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={data.prediction_trend}>
              <defs>
                <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Area type="monotone" dataKey="total" stroke="#0ea5e9" fill="url(#g1)" name="Total Scans" />
              <Area type="monotone" dataKey="pneumonia" stroke="#ef4444" fill="none" strokeDasharray="4 2" name="Pneumonia" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Two charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Severity */}
          <div className="rounded-2xl border border-border bg-card p-5">
            <h3 className="text-sm font-bold text-foreground mb-4">Severity Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={sevData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {sevData.map((e, i) => <Cell key={i} fill={e.color} />)}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Model usage */}
          <div className="rounded-2xl border border-border bg-card p-5">
            <h3 className="text-sm font-bold text-foreground mb-4">Model Usage</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={modelData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis type="number" tick={{ fontSize: 10 }} />
                <YAxis type="category" dataKey="model" tick={{ fontSize: 10 }} width={90} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {modelData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}
