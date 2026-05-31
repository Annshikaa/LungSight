"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { BarChart3, Trophy } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { getBenchmarks, type BenchmarkResponse } from "@/lib/api";
import { formatPercent } from "@/lib/utils";

const MODEL_COLORS = ["#0ea5e9", "#8b5cf6", "#22c55e", "#f59e0b"];
const RANK_LABELS = ["", "🥇", "🥈", "🥉"];

export default function BenchmarkPage() {
  const [benchmarks, setBenchmarks] = useState<BenchmarkResponse[]>([]);

  useEffect(() => {
    getBenchmarks()
      .then((b) => setBenchmarks([...b].sort((a, z) => z.roc_auc - a.roc_auc)))
      .catch(console.error);
  }, []);

  return (
    <div className="flex flex-col min-h-full">
      <Header title="Model Benchmark" />
      <div className="flex-1 p-6 space-y-6">

        {/* Leaderboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {benchmarks.map((b, i) => (
            <motion.div
              key={b.model_name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="rounded-2xl border border-border bg-card p-5 shadow-sm"
            >
              <div className="flex items-start justify-between mb-4">
                <div
                  className="flex h-10 w-10 items-center justify-center rounded-xl text-white text-xs font-bold"
                  style={{ background: MODEL_COLORS[i] }}
                >
                  #{i + 1}
                </div>
                {i < 3 && <span className="text-2xl">{RANK_LABELS[i + 1]}</span>}
              </div>
              <h3 className="font-bold text-foreground mb-3">{b.model_name}</h3>
              <div className="space-y-2">
                {[
                  { label: "Accuracy",  value: b.accuracy },
                  { label: "F1 Score",  value: b.f1_score },
                  { label: "ROC-AUC",   value: b.roc_auc },
                  { label: "PR-AUC",    value: b.pr_auc },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-muted-foreground">{label}</span>
                      <span className="font-semibold text-foreground">{value.toFixed(4)}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${value * 100}%`, background: MODEL_COLORS[i] }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-lg bg-muted px-2 py-1.5 text-center">
                  <div className="text-muted-foreground">Inf. Time</div>
                  <div className="font-bold text-foreground">{b.avg_inference_time_ms} ms</div>
                </div>
                <div className="rounded-lg bg-muted px-2 py-1.5 text-center">
                  <div className="text-muted-foreground">Size</div>
                  <div className="font-bold text-foreground">{b.model_size_mb} MB</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Detailed table */}
        <div className="rounded-2xl border border-border bg-card overflow-hidden">
          <div className="flex items-center gap-2 p-5 border-b border-border">
            <Trophy className="h-4 w-4 text-amber-500" />
            <h3 className="text-sm font-bold text-foreground">Full Metrics Table</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  {["Rank", "Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC", "Specificity*", "Params", "Size", "Inf.Time"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {benchmarks.map((b, i) => (
                  <tr key={b.model_name} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3">
                      <span className="text-lg">{RANK_LABELS[i + 1] || `#${i + 1}`}</span>
                    </td>
                    <td className="px-4 py-3 font-bold text-foreground">{b.model_name}</td>
                    <td className="px-4 py-3">{formatPercent(b.accuracy * 100)}</td>
                    <td className="px-4 py-3">{formatPercent(b.precision * 100)}</td>
                    <td className="px-4 py-3">{formatPercent(b.recall * 100)}</td>
                    <td className="px-4 py-3">{formatPercent(b.f1_score * 100)}</td>
                    <td className="px-4 py-3 font-bold text-medical-600">{b.roc_auc.toFixed(4)}</td>
                    <td className="px-4 py-3">{b.pr_auc.toFixed(4)}</td>
                    <td className="px-4 py-3 text-muted-foreground">—</td>
                    <td className="px-4 py-3 text-muted-foreground">{(b.parameter_count / 1e6).toFixed(2)}M</td>
                    <td className="px-4 py-3 text-muted-foreground">{b.model_size_mb} MB</td>
                    <td className="px-4 py-3 text-muted-foreground">{b.avg_inference_time_ms} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-5 py-3 bg-muted/20 border-t border-border">
            <p className="text-xs text-muted-foreground">* Specificity computed on held-out test set from Chest X-Ray Pneumonia Dataset (Kaggle). Results may vary with different splits.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
