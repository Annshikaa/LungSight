"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Activity,
  BarChart3,
  Brain,
  ChevronRight,
  Eye,
  FileText,
  Wind,
  Shield,
  Stethoscope,
  User,
  Zap,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Multi-Model AI",
    description: "DenseNet121, EfficientNetB3, ResNet50, VGG16 — with weighted ensemble prediction.",
    color: "text-violet-500",
    bg: "bg-violet-100 dark:bg-violet-900/30",
  },
  {
    icon: Eye,
    title: "Grad-CAM Explainability",
    description: "Grad-CAM, Grad-CAM++, Saliency Maps, Integrated Gradients — see exactly what the AI sees.",
    color: "text-orange-500",
    bg: "bg-orange-100 dark:bg-orange-900/30",
  },
  {
    icon: Wind,
    title: "U-Net Segmentation",
    description: "Deep learning lung segmentation extracts ROI for precise, focused analysis.",
    color: "text-medical-500",
    bg: "bg-medical-100 dark:bg-medical-900/30",
  },
  {
    icon: Activity,
    title: "Severity Assessment",
    description: "AI-driven severity scoring from Normal to Critical with clinical recommendations.",
    color: "text-red-500",
    bg: "bg-red-100 dark:bg-red-900/30",
  },
  {
    icon: Shield,
    title: "Uncertainty Quantification",
    description: "Monte Carlo Dropout provides confidence, variance, and reliability indicators.",
    color: "text-green-500",
    bg: "bg-green-100 dark:bg-green-900/30",
  },
  {
    icon: FileText,
    title: "PDF Report Generation",
    description: "Professional diagnostic reports with all findings, heatmaps, and clinical notes.",
    color: "text-amber-500",
    bg: "bg-amber-100 dark:bg-amber-900/30",
  },
];

const stats = [
  { label: "Model Accuracy", value: "95.1%", sub: "EfficientNetB3 on test set" },
  { label: "ROC-AUC",        value: "0.984", sub: "Best model performance" },
  { label: "Inference Time", value: "42 ms", sub: "Per X-ray analysis" },
  { label: "Architectures",  value: "4+1",   sub: "Models + Ensemble" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="sticky top-0 z-50 flex h-16 items-center justify-between border-b border-white/10 glass-panel px-6 lg:px-12">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl gradient-medical">
            <Wind className="h-5 w-5 text-white" />
          </div>
          <span className="text-lg font-bold text-foreground">LungSight AI</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors">
            Clinician Login
          </Link>
          <Link
            href="/login"
            className="flex items-center gap-2 rounded-lg gradient-medical px-4 py-2 text-sm font-semibold text-white shadow hover:opacity-90 transition"
          >
            <User className="h-4 w-4" />
            Patient Portal
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden py-32 px-6 lg:px-12 bg-grid-pattern">
        {/* Animated Background Gradients */}
        <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-medical-500/20 blur-[100px] animate-pulse-slow mix-blend-screen" />
        <div className="absolute bottom-1/4 right-1/4 h-[28rem] w-[28rem] rounded-full bg-violet-500/20 blur-[100px] animate-pulse-slow mix-blend-screen" style={{ animationDelay: '1s' }} />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background" />
        
        <div className="relative mx-auto max-w-4xl text-center z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center gap-2 rounded-full border border-medical-200 bg-medical-100 px-4 py-1.5 text-xs font-semibold text-medical-700 dark:bg-medical-900/40 dark:text-medical-300 mb-6">
              <span className="h-1.5 w-1.5 rounded-full bg-medical-500 animate-pulse" />
              Research-Grade AI Platform
            </span>

            <h1 className="text-5xl lg:text-7xl font-extrabold tracking-tight text-foreground mb-6">
              Explainable{" "}
              <span className="bg-gradient-to-r from-medical-500 to-medical-700 bg-clip-text text-transparent">
                Pneumonia
              </span>{" "}
              Detection
            </h1>

            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
              AI-powered chest X-ray analysis with Grad-CAM explainability, U-Net lung segmentation,
              severity assessment, and uncertainty quantification — built for radiologists and researchers.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/login"
                className="flex items-center justify-center gap-2 rounded-xl gradient-medical px-8 py-4 text-base font-bold text-white shadow-lg hover:opacity-90 transition"
              >
                <Stethoscope className="h-5 w-5" />
                Access Clinical Dashboard
                <ChevronRight className="h-5 w-5" />
              </Link>
              <Link
                href="/login"
                className="flex items-center justify-center gap-2 rounded-xl border border-border bg-card px-8 py-4 text-base font-bold text-foreground hover:bg-muted transition"
              >
                <User className="h-5 w-5" />
                Patient Portal Access
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-border bg-card py-12 px-6 lg:px-12">
        <div className="mx-auto max-w-5xl grid grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ scale: 1.05 }}
              className="text-center glass-panel p-6 rounded-2xl relative overflow-hidden group"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="text-4xl font-extrabold text-medical-600 dark:text-medical-400 relative z-10">{s.value}</div>
              <div className="text-sm font-semibold text-foreground mt-1">{s.label}</div>
              <div className="text-xs text-muted-foreground">{s.sub}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6 lg:px-12">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-extrabold text-foreground mb-4">
              Complete AI Diagnostic Pipeline
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              From raw X-ray to comprehensive clinical report — every step powered by state-of-the-art deep learning.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => {
              const Icon = f.icon;
              return (
                <motion.div
                  key={f.title}
                  initial={{ opacity: 0, y: 24 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08 }}
                  whileHover={{ y: -8 }}
                  className="rounded-2xl border border-white/10 glass-panel p-6 shadow-xl transition-all duration-300 relative group overflow-hidden"
                >
                  <div className={`absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-300 ${f.bg.split(' ')[0]}`} />
                  <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl ${f.bg}`}>
                    <Icon className={`h-6 w-6 ${f.color}`} />
                  </div>
                  <h3 className="text-base font-bold text-foreground mb-2">{f.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{f.description}</p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Pipeline visualization */}
      <section className="border-t border-border bg-card py-20 px-6 lg:px-12">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-extrabold text-foreground mb-12">AI Pipeline</h2>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {[
              "Chest X-Ray Upload",
              "Image Enhancement",
              "Lung Segmentation",
              "ROI Extraction",
              "Deep Learning Classification",
              "Grad-CAM Explainability",
              "Severity Assessment",
              "PDF Report",
            ].map((step, i) => (
              <div key={step} className="flex items-center gap-3">
                <div className="rounded-lg border border-medical-200 bg-medical-50 dark:bg-medical-900/20 px-3 py-2 text-xs font-medium text-medical-700 dark:text-medical-300">
                  {step}
                </div>
                {i < 7 && <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 lg:px-12 text-center">
        <div className="mx-auto max-w-2xl">
          <h2 className="text-3xl font-extrabold text-foreground mb-4">Ready to analyze?</h2>
          <p className="text-muted-foreground mb-8">
            Access your secure portal to view AI diagnostic reports or initiate a new analysis.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-xl gradient-medical px-10 py-4 text-lg font-bold text-white shadow-xl hover:opacity-90 transition"
          >
            <Shield className="h-5 w-5" />
            Secure Login
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card py-8 px-6 lg:px-12 text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Wind className="h-4 w-4 text-medical-500" />
          <span className="text-sm font-bold text-foreground">LungSight AI</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Research-grade AI tool — not a certified medical device. Always consult a qualified physician.
        </p>
      </footer>
    </div>
  );
}
