import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 120_000,
});

// Attach JWT token from localStorage
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("ls_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ──────────────────────────────────────────────────────────────────────────────
// Types (mirror backend Pydantic schemas)
// ──────────────────────────────────────────────────────────────────────────────

export interface SeverityInfo {
  score: number;
  level: "Normal" | "Mild" | "Moderate" | "Severe" | "Critical";
  color: string;
  recommendations: string[];
  clinical_summary: string;
}

export interface UncertaintyInfo {
  confidence_percent: number;
  uncertainty_percent: number;
  variance: number;
  entropy: number;
  reliability: "High" | "Medium" | "Low";
  reliability_color: string;
}

export interface HeatmapInfo {
  method: string;
  heatmap_b64: string;
  overlay_b64: string;
  bounding_box?: { x: number; y: number; w: number; h: number } | null;
  activation_coverage: number;
}

export interface SegmentationInfo {
  mask_b64: string;
  overlay_b64: string;
  roi_b64: string;
  lung_area_pixels: number;
  lung_area_percentage: number;
  dice_score?: number | null;
  iou_score?: number | null;
}

export interface PredictionResponse {
  scan_id: string;
  prediction_id: string;
  label: "NORMAL" | "PNEUMONIA";
  confidence: number;
  pneumonia_probability: number;
  normal_probability: number;
  model_used: string;
  inference_time_ms: number;
  individual_predictions?: Record<string, number> | null;
  ensemble_agreement?: number | null;
  severity: SeverityInfo;
  uncertainty: UncertaintyInfo;
  heatmaps: Record<string, HeatmapInfo>;
  segmentation?: SegmentationInfo | null;
  original_image_b64: string;
  enhanced_image_b64: string;
  dicom_metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface AnalyticsResponse {
  total_scans: number;
  pneumonia_cases: number;
  normal_cases: number;
  average_confidence: number;
  average_severity_score: number;
  model_accuracy_estimate: number;
  severity_distribution: Record<string, number>;
  prediction_trend: Array<{ date: string; total: number; pneumonia: number; normal: number }>;
  model_usage: Record<string, number>;
}

export interface BenchmarkResponse {
  model_name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  pr_auc: number;
  avg_inference_time_ms: number;
  model_size_mb: number;
  parameter_count: number;
  confusion_matrix: number[][];
}

// ──────────────────────────────────────────────────────────────────────────────
// API functions
// ──────────────────────────────────────────────────────────────────────────────

export async function predictXRay(
  file: File,
  model: string = "Ensemble",
  runSegmentation: boolean = true,
  xaiMethods: string = "gradcam,gradcam_pp,saliency",
): Promise<PredictionResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("model", model);
  form.append("run_segmentation", String(runSegmentation));
  form.append("xai_methods", xaiMethods);

  const { data } = await api.post<PredictionResponse>("/predict", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getAnalytics(): Promise<AnalyticsResponse> {
  const { data } = await api.get<AnalyticsResponse>("/analytics");
  return data;
}

export async function getBenchmarks(): Promise<BenchmarkResponse[]> {
  const { data } = await api.get<BenchmarkResponse[]>("/benchmark");
  return data;
}

export async function getModels() {
  const { data } = await api.get("/models");
  return data;
}

export async function getHealth() {
  const { data } = await api.get("/health");
  return data;
}

export async function generateReport(payload: {
  prediction_id: string;
  patient_name?: string;
  patient_id?: string;
  patient_age?: string;
  patient_sex?: string;
  referring_doctor?: string;
  doctor_notes?: string;
  label?: string;
  confidence?: number;
  severity_level?: string;
  severity_score?: number;
  model_used?: string;
  inference_time_ms?: number;
  uncertainty_percent?: number;
  reliability?: string;
  clinical_summary?: string;
  recommendations?: string[];
}): Promise<Blob> {
  const { data } = await api.post("/generate-report", payload, {
    responseType: "blob",
  });
  return data;
}
