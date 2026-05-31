"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Download, FileText, Loader2, Send } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { generateReport } from "@/lib/api";
import { downloadBlob } from "@/lib/utils";

export default function ReportsPage() {
  const [form, setForm] = useState({
    prediction_id: "",
    patient_name:  "Anonymous Patient",
    patient_id:    "PT-001",
    patient_age:   "45",
    patient_sex:   "M",
    referring_doctor: "Dr. Smith",
    doctor_notes:  "",
  });
  const [generating, setGenerating] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const blob = await generateReport(form);
      downloadBlob(blob, `lungsight_report_${form.prediction_id || "demo"}.pdf`);
      toast.success("Report downloaded!");
    } catch {
      toast.error("Failed to generate report. Make sure the backend is running.");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="flex flex-col min-h-full">
      <Header title="Report Generator" />
      <div className="flex-1 p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="rounded-2xl border border-border bg-card p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-medical-100 dark:bg-medical-900/40">
                <FileText className="h-5 w-5 text-medical-600" />
              </div>
              <div>
                <h2 className="text-base font-bold text-foreground">Generate PDF Report</h2>
                <p className="text-xs text-muted-foreground">Professional diagnostic report with all findings</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Prediction ID</label>
                <input name="prediction_id" value={form.prediction_id} onChange={handleChange}
                  placeholder="From a previous prediction (leave blank for demo)"
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-medical-500" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Patient Name</label>
                  <input name="patient_name" value={form.patient_name} onChange={handleChange}
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Patient ID</label>
                  <input name="patient_id" value={form.patient_id} onChange={handleChange}
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Age</label>
                  <input name="patient_age" value={form.patient_age} onChange={handleChange}
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Sex</label>
                  <select name="patient_sex" value={form.patient_sex} onChange={handleChange}
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500">
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="O">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Referring Physician</label>
                <input name="referring_doctor" value={form.referring_doctor} onChange={handleChange}
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500" />
              </div>

              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Physician Notes</label>
                <textarea name="doctor_notes" value={form.doctor_notes} onChange={handleChange}
                  rows={4} placeholder="Additional clinical observations, treatment notes…"
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-medical-500 resize-none" />
              </div>

              <button
                onClick={handleGenerate}
                disabled={generating}
                className="w-full rounded-xl gradient-medical py-3.5 text-sm font-bold text-white shadow hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
              >
                {generating ? (
                  <><Loader2 className="h-4 w-4 animate-spin" /> Generating PDF…</>
                ) : (
                  <><Download className="h-4 w-4" /> Generate & Download PDF</>
                )}
              </button>
            </div>
          </div>

          {/* Report features */}
          <div className="rounded-2xl border border-border bg-card p-6">
            <h3 className="text-sm font-bold text-foreground mb-4">Report Contents</h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                "Patient Information",
                "AI Diagnosis",
                "Confidence Score",
                "Severity Assessment",
                "Grad-CAM Heatmaps",
                "Imaging Overlays",
                "Clinical Summary",
                "Recommendations",
                "Physician Notes",
                "Disclaimer",
                "Hospital Branding",
                "Unique Report ID",
              ].map((item) => (
                <div key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                  <div className="h-1.5 w-1.5 rounded-full bg-medical-500 flex-shrink-0" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
