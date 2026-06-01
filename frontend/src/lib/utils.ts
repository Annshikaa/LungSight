import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatConfidence(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatMs(ms: number): string {
  return ms < 1000 ? `${ms.toFixed(1)} ms` : `${(ms / 1000).toFixed(2)} s`;
}

export function severityColor(level: string): string {
  const map: Record<string, string> = {
    Normal:   "text-green-600 dark:text-green-400",
    Mild:     "text-lime-600 dark:text-lime-400",
    Moderate: "text-amber-600 dark:text-amber-400",
    Severe:   "text-red-600 dark:text-red-400",
    Critical: "text-red-900 dark:text-red-300",
  };
  return map[level] ?? "text-gray-600";
}

export function severityBg(level: string): string {
  const map: Record<string, string> = {
    Normal:   "bg-green-100 dark:bg-green-900/30 border-green-200",
    Mild:     "bg-lime-100 dark:bg-lime-900/30 border-lime-200",
    Moderate: "bg-amber-100 dark:bg-amber-900/30 border-amber-200",
    Severe:   "bg-red-100 dark:bg-red-900/30 border-red-200",
    Critical: "bg-red-200 dark:bg-red-900/50 border-red-400",
  };
  return map[level] ?? "bg-gray-100 border-gray-200";
}

export function predictionColor(label: string): string {
  return label === "PNEUMONIA"
    ? "text-red-600 dark:text-red-400"
    : "text-green-600 dark:text-green-400";
}

export function predictionBadgeClass(label: string): string {
  return label === "PNEUMONIA"
    ? "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border border-red-200"
    : "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300 border border-green-200";
}

export function b64ToImgSrc(b64: string): string {
  return `data:image/png;base64,${b64}`;
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}
