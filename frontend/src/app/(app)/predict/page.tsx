/* eslint-disable @next/next/no-img-element */
"use client";

import { useCallback, useState, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Download,
  Eye,
  FileImage,
  Loader2,
  Wind,
  Shield,
  Stethoscope,
  Upload,
  User,
  Zap,
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import {
  predictXRay,
  generateReport,
  type PredictionResponse,
} from "@/lib/api";
import {
  b64ToImgSrc,
  downloadBlob,
  formatMs,
  formatPercent,
  predictionBadgeClass,
  severityBg,
  severityColor,
} from "@/lib/utils";

const MODELS = ["Ensemble", "DenseNet121", "EfficientNetB3", "ResNet50", "VGG16"];
const XAI_METHODS = ["gradcam", "gradcam_pp", "saliency", "integrated_gradients"];
const XAI_LABELS: Record<string, string> = {
  gradcam:               "Grad-CAM",
  gradcam_pp:            "Grad-CAM++",
  saliency:              "Saliency Map",
  integrated_gradients:  "Integrated Gradients",
};

// ──────────────────────────────────────────────────────────────────────────────
// Sub-components
// ──────────────────────────────────────────────────────────────────────────────

function InfoBadge({ label, value, icon: Icon, className = "" }: {
  label: string; value: string | number; icon: React.ElementType; className?: string;
}) {
  return (
    <div className={`rounded-xl border border-border bg-card p-4 ${className}`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon className="h-4 w-4 text-muted-foreground" />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <div className="text-xl font-extrabold text-foreground">{value}</div>
    </div>
  );
}

function SeverityGauge({ score, level, color }: { score: number; level: string; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-2">
        <span className="font-semibold text-foreground">Severity: <span style={{ color }}>{level}</span></span>
        <span className="font-bold text-foreground">{score}/100</span>
      </div>
      <div className="h-3 rounded-full bg-muted overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="h-full rounded-full"
          style={{ background: color }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
        <span>Normal</span>
        <span>Mild</span>
        <span>Moderate</span>
        <span>Severe</span>
        <span>Critical</span>
      </div>
    </div>
  );
}

function ImageCard({ b64, label }: { b64: string; label: string }) {
  return (
    <div className="rounded-xl overflow-hidden border border-border bg-muted">
      <img src={b64ToImgSrc(b64)} alt={label} className="w-full object-cover aspect-square" />
      <div className="px-3 py-1.5 text-xs font-medium text-muted-foreground text-center bg-card border-t border-border">
        {label}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────────
// Main page
// ──────────────────────────────────────────────────────────────────────────────

export default function PredictPage() {
  const [patientName, setPatientName] = useState("");
  const [patientId, setPatientId] = useState("");
  const [patientAge, setPatientAge] = useState("");
  const [patientSex, setPatientSex] = useState("");
  const [doctorNotes, setDoctorNotes] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState("Ensemble");
  const [selectedMethods, setSelectedMethods] = useState(["gradcam", "gradcam_pp", "saliency"]);
  const [runSeg, setRunSeg] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [activeHeatmap, setActiveHeatmap] = useState("gradcam");
  const [showRec, setShowRec] = useState(true);
  const [generatingReport, setGeneratingReport] = useState(false);
  const router = useRouter();

  const handleNotesChange = (val: string) => {
    setDoctorNotes(val);
    if (result) {
      const existing = JSON.parse(localStorage.getItem("ls_predictions") || "[]");
      if (existing.length > 0) {
        existing[0].notes = val || "No physician notes added.";
        localStorage.setItem("ls_predictions", JSON.stringify(existing));
      }
    }
  };

  useEffect(() => {
    if (localStorage.getItem("ls_user_role") === "patient") {
      router.push("/dashboard");
    }
    // Auto-assign a random patient ID on load so the doctor doesn't have to invent one
    setPatientId(`ACC-${Math.floor(Math.random()*90000)+10000}-${String.fromCharCode(65+Math.floor(Math.random()*26))}`);
  }, [router]);

  // Drop zone
  const onDrop = useCallback((accepted: File[]) => {
    const file = accepted[0];
    if (!file) return;
    setSelectedFile(file);
    setResult(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
    toast.success(`Loaded: ${file.name}`);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".png", ".jpg", ".jpeg"], "application/dicom": [".dcm", ".dicom"] },
    multiple: false,
    maxSize: 50 * 1024 * 1024,
  });

  // Toggle XAI method selection
  const toggleMethod = (m: string) =>
    setSelectedMethods((prev) =>
      prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m],
    );

  // Run prediction
  const runPrediction = async () => {
    if (!selectedFile) { toast.error("Please select an X-ray image first."); return; }
    if (selectedMethods.length === 0) { toast.error("Select at least one XAI method."); return; }

    setLoading(true);
    try {
      const res = await predictXRay(
        selectedFile,
        selectedModel,
        runSeg,
        selectedMethods.join(","),
      );
      setResult(res);
      setActiveHeatmap(selectedMethods[0]);
      
      // Save to local storage history
      const existing = JSON.parse(localStorage.getItem("ls_predictions") || "[]");
      const currentDoctor = localStorage.getItem("ls_user_name") || "Dr. Anshika Jain";
      const newScan = {
        id: `SCN-${Math.floor(Math.random()*90000)+10000}`,
        patientId: patientId || `ACC-${Math.floor(Math.random()*90000)+10000}`,
        patient: patientName || "Anonymous Patient",
        age: patientAge || "N/A",
        sex: patientSex || "N/A",
        doctor: currentDoctor,
        notes: doctorNotes || "No physician notes added.",
        status: res.severity.level,
        type: res.label === "NORMAL" ? "Clear" : "Pneumonia",
        confidence: `${(res.confidence * 100).toFixed(1)}%`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        timestamp: Date.now(),
        inference_time_ms: res.inference_time_ms
      };
      localStorage.setItem("ls_predictions", JSON.stringify([newScan, ...existing]));

      toast.success("Analysis complete!");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Prediction failed. Is the backend running?";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  // Download report
  const handleReport = async () => {
    if (!result) return;
    setGeneratingReport(true);
    try {
      const blob = await generateReport({
        prediction_id: result.prediction_id,
        patient_name: patientName || "Anonymous Patient",
        patient_id: patientId || "N/A",
        patient_age: patientAge || "N/A",
        patient_sex: patientSex || "N/A",
        referring_doctor: localStorage.getItem("ls_user_name") || "Dr. Anshika Jain",
        doctor_notes: doctorNotes || "",
        label: result.label,
        confidence: result.confidence,
        severity_level: result.severity.level,
        severity_score: result.severity.score,
        model_used: result.model_used,
        inference_time_ms: result.inference_time_ms,
        clinical_summary: result.severity.clinical_summary,
        recommendations: result.severity.recommendations,
      });
      downloadBlob(blob, `lungsight_report_${result.prediction_id.slice(0, 8)}.pdf`);
      toast.success("Report downloaded!");
    } catch {
      toast.error("Report generation failed.");
    } finally {
      setGeneratingReport(false);
    }
  };

  return (
    <div className="flex flex-col min-h-full">
      <Header title="X-Ray Analysis" />

      <div className="flex-1 p-6">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

          {/* ── Left panel: Upload + Settings ─────────────────────────── */}
          <div className="xl:col-span-1 space-y-5">

            {/* Patient Details */}
            <div className="rounded-2xl border border-border bg-card p-5">
              <h3 className="text-sm font-bold text-foreground mb-4 flex items-center gap-2">
                <User className="h-4 w-4 text-blue-500" /> Patient Information
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-muted-foreground mb-1.5">Patient Name</label>
                  <input
                    type="text"
                    value={patientName}
                    onChange={(e) => setPatientName(e.target.value)}
                    placeholder="e.g., M. Ramirez"
                    className="w-full bg-background/50 border border-border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-medical-500 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-muted-foreground mb-1.5">Patient ID</label>
                  <input
                    type="text"
                    value={patientId}
                    onChange={(e) => setPatientId(e.target.value)}
                    placeholder="e.g., ACC-8921-X"
                    className="w-full bg-background/50 border border-border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-medical-500 transition-all"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-muted-foreground mb-1.5">Age</label>
                    <input
                      type="number"
                      value={patientAge}
                      onChange={(e) => setPatientAge(e.target.value)}
                      placeholder="e.g. 45"
                      className="w-full bg-background/50 border border-border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-medical-500 transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-muted-foreground mb-1.5">Sex</label>
                    <select
                      value={patientSex}
                      onChange={(e) => setPatientSex(e.target.value)}
                      className="w-full bg-background/50 border border-border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-medical-500 transition-all"
                    >
                      <option value="">Select...</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-muted-foreground mb-1.5">Physician Notes (for PDF)</label>
                  <textarea
                    value={doctorNotes}
                    onChange={(e) => handleNotesChange(e.target.value)}
                    rows={2}
                    placeholder="Clinical observations..."
                    className="w-full bg-background/50 border border-border rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-medical-500 transition-all resize-none"
                  />
                </div>
              </div>
            </div>

            {/* Upload */}
            <div className="rounded-2xl border border-border bg-card p-5">
              <h3 className="text-sm font-bold text-foreground mb-4 flex items-center gap-2">
                <Upload className="h-4 w-4 text-medical-500" /> Upload X-Ray
              </h3>

              <div
                {...getRootProps()}
                className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-all duration-300 transform hover:scale-[1.01]
                  ${isDragActive ? "border-medical-500 bg-medical-500/10 scale-[1.02]" : "border-border hover:border-medical-400 hover:bg-muted/30"}`}
              >
                <input {...getInputProps()} />
                {preview ? (
                  <img src={preview} alt="preview" className="mx-auto max-h-40 rounded-lg object-contain" />
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <FileImage className="h-12 w-12 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium text-foreground">Drop X-Ray here</p>
                      <p className="text-xs text-muted-foreground mt-0.5">PNG, JPG, JPEG, DICOM — max 50 MB</p>
                    </div>
                  </div>
                )}
              </div>
              {selectedFile && (
                <p className="mt-2 text-xs text-muted-foreground text-center truncate">{selectedFile.name}</p>
              )}
            </div>

            {/* Model selection */}
            <div className="rounded-2xl border border-border bg-card p-5">
              <h3 className="text-sm font-bold text-foreground mb-3 flex items-center gap-2">
                <Brain className="h-4 w-4 text-violet-500" /> Model Selection
              </h3>
              <div className="space-y-2">
                {MODELS.map((m) => (
                  <button
                    key={m}
                    onClick={() => setSelectedModel(m)}
                    className={`w-full rounded-lg px-3 py-2.5 text-sm text-left transition-colors flex items-center justify-between
                      ${selectedModel === m
                        ? "bg-medical-100 text-medical-700 dark:bg-medical-900/40 dark:text-medical-300 font-semibold"
                        : "hover:bg-muted text-muted-foreground"}`}
                  >
                    {m}
                    {m === "Ensemble" && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-medical-500 text-white">Recommended</span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* XAI methods */}
            <div className="rounded-2xl border border-border bg-card p-5">
              <h3 className="text-sm font-bold text-foreground mb-3 flex items-center gap-2">
                <Eye className="h-4 w-4 text-orange-500" /> Explainability Methods
              </h3>
              <div className="space-y-2">
                {XAI_METHODS.map((m) => (
                  <label key={m} className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedMethods.includes(m)}
                      onChange={() => toggleMethod(m)}
                      className="h-4 w-4 rounded border-border text-medical-500"
                    />
                    <span className="text-sm text-foreground">{XAI_LABELS[m]}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Options */}
            <div className="rounded-2xl border border-border bg-card p-5">
              <h3 className="text-sm font-bold text-foreground mb-3 flex items-center gap-2">
                <Wind className="h-4 w-4 text-medical-500" /> Pipeline Options
              </h3>
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={runSeg} onChange={(e) => setRunSeg(e.target.checked)}
                  className="h-4 w-4 rounded border-border text-medical-500" />
                <div>
                  <p className="text-sm font-medium text-foreground">Lung Segmentation</p>
                  <p className="text-xs text-muted-foreground">Run U-Net to extract lung ROI</p>
                </div>
              </label>
            </div>

            {/* Analyze button */}
            <button
              onClick={runPrediction}
              disabled={loading || !selectedFile}
              className="w-full rounded-xl bg-gradient-to-r from-medical-600 to-medical-500 py-4 text-base font-bold text-white shadow-[0_0_20px_rgba(14,165,233,0.3)] hover:shadow-[0_0_30px_rgba(14,165,233,0.5)] transform hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <><Loader2 className="h-5 w-5 animate-spin" /> Analyzing…</>
              ) : (
                <><Zap className="h-5 w-5" /> Run AI Analysis</>
              )}
            </button>
          </div>

          {/* ── Right panel: Results ───────────────────────────────────── */}
          <div className="xl:col-span-2 space-y-5">
            <AnimatePresence mode="wait">
              {!result && !loading && (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex h-80 items-center justify-center rounded-2xl border-2 border-dashed border-border"
                >
                  <div className="text-center">
                    <Stethoscope className="mx-auto h-16 w-16 text-muted-foreground/30 mb-4" />
                    <p className="text-muted-foreground text-sm">Upload an X-ray and click Analyze to see results</p>
                  </div>
                </motion.div>
              )}

              {loading && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex h-80 flex-col items-center justify-center rounded-2xl border border-border bg-card gap-4"
                >
                  <div className="h-16 w-16 rounded-full border-4 border-medical-100 border-t-medical-500 animate-spin" />
                  <div className="text-center">
                    <p className="font-semibold text-foreground">Running AI Pipeline</p>
                    <p className="text-xs text-muted-foreground mt-1">Segmentation → Classification → Explainability</p>
                  </div>
                </motion.div>
              )}

              {result && (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-5"
                >
                  {/* Prediction header */}
                  <div className={`rounded-2xl border p-6 ${severityBg(result.severity.level)}`}>
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-3 mb-2">
                          {result.label === "PNEUMONIA" ? (
                            <AlertTriangle className="h-8 w-8 text-red-500" />
                          ) : (
                            <CheckCircle2 className="h-8 w-8 text-green-500" />
                          )}
                          <div>
                            <span className={`text-3xl font-extrabold ${result.label === "PNEUMONIA" ? "text-red-700 dark:text-red-400" : "text-green-700 dark:text-green-400"}`}>
                              {result.label}
                            </span>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className={`text-sm px-3 py-1 rounded-full font-semibold ${predictionBadgeClass(result.label)}`}>
                                {(result.confidence * 100).toFixed(1)}% confidence
                              </span>
                              <span className="text-xs text-muted-foreground flex items-center gap-1">
                                <Clock className="h-3 w-3" /> {formatMs(result.inference_time_ms)}
                              </span>
                            </div>
                          </div>
                        </div>
                        <p className="text-sm text-muted-foreground">Model: {result.model_used}</p>
                        {(patientName || patientId) && (
                          <p className="text-sm font-medium text-foreground mt-2">
                            Patient: {patientName || "Unknown"} <span className="text-muted-foreground font-normal">({patientId || "N/A"})</span>
                          </p>
                        )}
                      </div>
                      <button
                        onClick={handleReport}
                        disabled={generatingReport}
                        className="flex items-center gap-2 rounded-xl bg-white dark:bg-slate-800 px-4 py-2.5 text-sm font-semibold text-foreground shadow border border-border hover:bg-muted transition disabled:opacity-50"
                      >
                        {generatingReport
                          ? <Loader2 className="h-4 w-4 animate-spin" />
                          : <Download className="h-4 w-4" />}
                        Download Report
                      </button>
                    </div>

                    <div className="mt-5">
                      <SeverityGauge
                        score={result.severity.score}
                        level={result.severity.level}
                        color={result.severity.color}
                      />
                    </div>
                  </div>

                  {/* KPI row */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <InfoBadge label="Pneumonia Prob."  value={formatPercent(result.pneumonia_probability * 100)} icon={Activity} />
                    <InfoBadge label="Normal Prob."     value={formatPercent(result.normal_probability * 100)}    icon={CheckCircle2} />
                    <InfoBadge label="Uncertainty"      value={formatPercent(result.uncertainty.uncertainty_percent)} icon={AlertCircle} />
                    <InfoBadge label="Reliability"      value={result.uncertainty.reliability} icon={Shield} />
                  </div>

                  {/* Ensemble breakdown */}
                  {result.individual_predictions && (
                    <div className="rounded-2xl border border-border bg-card p-5">
                      <h3 className="text-sm font-bold text-foreground mb-3 flex items-center gap-2">
                        <Brain className="h-4 w-4 text-violet-500" /> Ensemble Model Agreement
                        {result.ensemble_agreement && (
                          <span className="ml-auto text-xs font-normal text-muted-foreground">
                            Agreement: {formatPercent(result.ensemble_agreement * 100)}
                          </span>
                        )}
                      </h3>
                      <div className="space-y-3">
                        {Object.entries(result.individual_predictions).map(([model, prob]) => (
                          <div key={model}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="font-medium text-foreground">{model}</span>
                              <span className="text-muted-foreground">{formatPercent(prob * 100)} pneumonia</span>
                            </div>
                            <div className="h-2 rounded-full bg-muted overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${prob * 100}%` }}
                                transition={{ duration: 0.8 }}
                                className="h-full rounded-full bg-medical-500"
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Images */}
                  <div className="rounded-2xl border border-border bg-card p-5">
                    <h3 className="text-sm font-bold text-foreground mb-4 flex items-center gap-2">
                      <Eye className="h-4 w-4 text-orange-500" /> Imaging Analysis
                    </h3>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                      <ImageCard b64={result.original_image_b64}  label="Original X-Ray" />
                      <ImageCard b64={result.enhanced_image_b64}  label="Enhanced" />
                      {result.segmentation && (
                        <>
                          <ImageCard b64={result.segmentation.overlay_b64} label="Segmentation Overlay" />
                          <ImageCard b64={result.segmentation.roi_b64}     label="Lung ROI" />
                        </>
                      )}
                    </div>
                    {result.segmentation && (
                      <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
                        <span>Lung area: {result.segmentation.lung_area_percentage.toFixed(1)}%</span>
                        {result.segmentation.dice_score && <span>Dice: {result.segmentation.dice_score.toFixed(3)}</span>}
                        {result.segmentation.iou_score  && <span>IoU: {result.segmentation.iou_score.toFixed(3)}</span>}
                      </div>
                    )}
                  </div>

                  {/* Heatmaps */}
                  <div className="rounded-2xl border border-border bg-card p-5">
                    <h3 className="text-sm font-bold text-foreground mb-4 flex items-center gap-2">
                      <Eye className="h-4 w-4 text-orange-500" /> Explainability Heatmaps
                    </h3>
                    {/* Method tabs */}
                    <div className="flex gap-2 mb-4 flex-wrap">
                      {Object.keys(result.heatmaps).map((method) => (
                        <button
                          key={method}
                          onClick={() => setActiveHeatmap(method)}
                          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors
                            ${activeHeatmap === method
                              ? "bg-medical-500 text-white"
                              : "bg-muted text-muted-foreground hover:bg-muted/80"}`}
                        >
                          {XAI_LABELS[method] ?? method}
                        </button>
                      ))}
                    </div>
                    {result.heatmaps[activeHeatmap] && (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <ImageCard b64={result.heatmaps[activeHeatmap].heatmap_b64} label="Activation Heatmap" />
                        <ImageCard b64={result.heatmaps[activeHeatmap].overlay_b64} label="Overlay on X-Ray" />
                      </div>
                    )}
                    {result.heatmaps[activeHeatmap] && (
                      <p className="mt-2 text-xs text-muted-foreground">
                        Activation coverage: {formatPercent(result.heatmaps[activeHeatmap].activation_coverage * 100)}
                        {result.heatmaps[activeHeatmap].bounding_box && (
                          <> · Bounding box: ({result.heatmaps[activeHeatmap].bounding_box!.x}, {result.heatmaps[activeHeatmap].bounding_box!.y}) {result.heatmaps[activeHeatmap].bounding_box!.w}×{result.heatmaps[activeHeatmap].bounding_box!.h}px</>
                        )}
                      </p>
                    )}
                  </div>

                  {/* Clinical summary & recommendations */}
                  <div className="rounded-2xl border border-border bg-card p-5">
                    <button
                      className="flex items-center justify-between w-full text-left"
                      onClick={() => setShowRec(!showRec)}
                    >
                      <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                        <Stethoscope className="h-4 w-4 text-medical-500" /> Clinical Summary & Recommendations
                      </h3>
                      {showRec ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
                    </button>
                    <AnimatePresence>
                      {showRec && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden"
                        >
                          <p className="mt-4 text-sm text-muted-foreground leading-relaxed">
                            {result.severity.clinical_summary}
                          </p>
                          <ul className="mt-4 space-y-2">
                            {result.severity.recommendations.map((r, i) => (
                              <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                                <CheckCircle2 className={`h-4 w-4 mt-0.5 flex-shrink-0 ${severityColor(result.severity.level)}`} />
                                {r}
                              </li>
                            ))}
                          </ul>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* DICOM metadata */}
                  {result.dicom_metadata && Object.keys(result.dicom_metadata).length > 0 && (
                    <div className="rounded-2xl border border-border bg-card p-5">
                      <h3 className="text-sm font-bold text-foreground mb-3">DICOM Metadata</h3>
                      <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
                        {Object.entries(result.dicom_metadata).slice(0, 12).map(([k, v]) => (
                          <div key={k} className="rounded-lg bg-muted px-3 py-2">
                            <p className="text-[10px] text-muted-foreground">{k}</p>
                            <p className="text-xs font-medium text-foreground truncate">{String(v)}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}
