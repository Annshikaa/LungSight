"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  CartesianGrid,
  Cell,
  Legend,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Header } from "@/components/layout/Header";
import { getBenchmarks, type BenchmarkResponse } from "@/lib/api";
import { formatPercent } from "@/lib/utils";

const MODEL_COLORS = ["#0ea5e9", "#8b5cf6", "#22c55e", "#f59e0b"];

export default function ResearchPage() {
  const [benchmarks, setBenchmarks] = useState<BenchmarkResponse[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    getBenchmarks().then(setBenchmarks).catch(console.error);
  }, []);

  if (!benchmarks.length) return (
    <div className="flex h-full items-center justify-center">
      <div className="h-10 w-10 rounded-full border-4 border-medical-200 border-t-medical-500 animate-spin" />
    </div>
  );

  const radarData = [
    "accuracy", "precision", "recall", "f1_score", "roc_auc", "pr_auc",
  ].map((metric) => ({
    metric: metric === "f1_score" ? "F1" : metric === "roc_auc" ? "ROC-AUC" : metric.charAt(0).toUpperCase() + metric.slice(1),
    ...Object.fromEntries(
      benchmarks.map((b) => [b.model_name, +(b[metric as keyof BenchmarkResponse] as number * 100).toFixed(1)]),
    ),
  }));

  const selectedBenchmark = benchmarks.find((b) => b.model_name === selected) ?? benchmarks[0];

  const cmLabels = ["True Normal", "True Pneumonia"];

  return (
    <div className="flex flex-col min-h-full">
      <Header title="Research & Analysis" />

      <div className="flex-1 p-6 space-y-6">
        {/* Radar chart */}
        <div className="rounded-2xl border border-border bg-card p-5">
          <h3 className="text-sm font-bold text-foreground mb-4">Model Comparison Radar</h3>
          <ResponsiveContainer width="100%" height={320}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11 }} />
              {benchmarks.map((b, i) => (
                <Radar
                  key={b.model_name}
                  name={b.model_name}
                  dataKey={b.model_name}
                  stroke={MODEL_COLORS[i]}
                  fill={MODEL_COLORS[i]}
                  fillOpacity={0.12}
                  dot={{ r: 3 }}
                />
              ))}
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} formatter={(v) => [`${v}%`]} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Side by side: inference time + model size */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="rounded-2xl border border-border bg-card p-5">
            <h3 className="text-sm font-bold text-foreground mb-4">Inference Time (ms)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={benchmarks.map((b, i) => ({ name: b.model_name, time: b.avg_inference_time_ms, fill: MODEL_COLORS[i] }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} unit=" ms" />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} formatter={(v) => [`${v} ms`]} />
                <Bar dataKey="time" radius={[4, 4, 0, 0]}>
                  {benchmarks.map((_, i) => <Cell key={i} fill={MODEL_COLORS[i]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-2xl border border-border bg-card p-5">
            <h3 className="text-sm font-bold text-foreground mb-4">Model Size (MB)</h3>
            <ResponsiveContainer width="100%" height={200}>
              <RadialBarChart
                data={benchmarks.map((b, i) => ({ name: b.model_name, size: b.model_size_mb, fill: MODEL_COLORS[i] }))}
                cx="50%" cy="50%" innerRadius="20%" outerRadius="80%"
              >
                <RadialBar dataKey="size" label={{ position: "insideStart", fill: "#fff", fontSize: 9 }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} formatter={(v) => [`${v} MB`]} />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Confusion matrices */}
        <div className="rounded-2xl border border-border bg-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-foreground">Confusion Matrix</h3>
            <div className="flex gap-2">
              {benchmarks.map((b, i) => (
                <button
                  key={b.model_name}
                  onClick={() => setSelected(b.model_name)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors
                    ${(selected ?? benchmarks[0]?.model_name) === b.model_name
                      ? "text-white"
                      : "bg-muted text-muted-foreground hover:bg-muted/80"}`}
                  style={{ background: (selected ?? benchmarks[0]?.model_name) === b.model_name ? MODEL_COLORS[i] : undefined }}
                >
                  {b.model_name}
                </button>
              ))}
            </div>
          </div>

          {selectedBenchmark && (
            <div className="flex justify-center">
              <div className="max-w-sm w-full">
                <div className="grid grid-cols-3 gap-0 text-center text-sm">
                  <div className="p-3" />
                  <div className="p-3 text-xs font-semibold text-muted-foreground">Pred. Normal</div>
                  <div className="p-3 text-xs font-semibold text-muted-foreground">Pred. Pneumonia</div>
                  {selectedBenchmark.confusion_matrix.map((row, ri) => (
                    <React.Fragment key={ri}>
                      <div className="p-3 text-xs font-semibold text-muted-foreground flex items-center justify-end pr-4">
                        {cmLabels[ri]}
                      </div>
                      {row.map((val, ci) => (
                        <motion.div
                          key={`cell-${ri}-${ci}`}
                          initial={{ scale: 0.8, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          className={`p-6 m-1 rounded-xl text-center font-extrabold text-xl
                            ${ri === ci
                              ? "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300"
                              : "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300"}`}
                        >
                          {val}
                          <div className="text-[10px] font-normal text-muted-foreground mt-1">
                            {ri === ci ? (ri === 0 ? "TN" : "TP") : (ri === 0 ? "FP" : "FN")}
                          </div>
                        </motion.div>
                      ))}
                    </React.Fragment>
                  ))}
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  {[
                    { label: "Accuracy",  value: formatPercent(selectedBenchmark.accuracy * 100) },
                    { label: "Precision", value: formatPercent(selectedBenchmark.precision * 100) },
                    { label: "Recall",    value: formatPercent(selectedBenchmark.recall * 100) },
                    { label: "F1 Score",  value: formatPercent(selectedBenchmark.f1_score * 100) },
                    { label: "ROC-AUC",   value: selectedBenchmark.roc_auc.toFixed(4) },
                    { label: "PR-AUC",    value: selectedBenchmark.pr_auc.toFixed(4) },
                  ].map(({ label, value }) => (
                    <div key={label} className="rounded-lg bg-muted px-3 py-2 text-center">
                      <div className="text-[10px] text-muted-foreground">{label}</div>
                      <div className="font-bold text-foreground">{value}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Architecture details */}
        <div className="rounded-2xl border border-border bg-card overflow-hidden">
          <div className="p-5 border-b border-border">
            <h3 className="text-sm font-bold text-foreground">Architecture Specifications</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  {["Model", "Parameters", "Size", "Inf. Time", "Backbone", "Head", "Best For"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {[
                  { model: "DenseNet121", params: "7.98M", size: "31.2 MB", time: "38.4 ms", backbone: "Dense connections", head: "FC+Dropout", best: "Feature reuse" },
                  { model: "EfficientNetB3", params: "12.23M", size: "48.6 MB", time: "42.1 ms", backbone: "Compound scaling", head: "FC+Dropout", best: "Accuracy/speed tradeoff" },
                  { model: "ResNet50", params: "25.56M", size: "97.8 MB", time: "31.8 ms", backbone: "Residual blocks", head: "FC+Dropout", best: "Robust baseline" },
                ].map((row) => (
                  <tr key={row.model} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-medium text-foreground">{row.model}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.params}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.size}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.time}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.backbone}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.head}</td>
                    <td className="px-4 py-3 text-muted-foreground">{row.best}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
