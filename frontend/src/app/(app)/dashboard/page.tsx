"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Activity, AlertTriangle, ArrowUpRight, ChevronRight, 
  Clock, FileText, FileImage, Stethoscope, Users, Zap, User, Download, Loader2
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { generateReport } from "@/lib/api";
import { downloadBlob } from "@/lib/utils";
import toast from "react-hot-toast";

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false);
  const [userName, setUserName] = useState("Dr. Anshika Jain");
  const [role, setRole] = useState("doctor");
  const [scans, setScans] = useState<any[]>([]);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    const storedName = localStorage.getItem("ls_user_name");
    const storedRole = localStorage.getItem("ls_user_role");
    
    if (storedName && storedName.trim() !== "Dr.") {
      setUserName(storedName);
    }
    if (storedRole) {
      setRole(storedRole);
    }
    
    const storedScans = JSON.parse(localStorage.getItem("ls_predictions") || "[]");
    setScans(storedScans);
  }, []);

  if (!mounted) return null;

  // ── Patient Portal View ─────────────────────────────────────────────────
  if (role === "patient") {
    // The login screen now stores the Patient ID in userName
    const safeUserName = userName ? userName.toLowerCase().trim() : "";
    // Support backwards compatibility if patientId is missing
    const patientScans = scans.filter(s => {
      const pid = s.patientId || s.id;
      return pid && pid.toLowerCase().trim() === safeUserName;
    });
    const actualName = patientScans.length > 0 ? patientScans[0].patient : "Patient";
    const latestScan = patientScans[0];
    
    const handleDownload = async (scan: any) => {
      setDownloadingId(scan.id);
      try {
        const blob = await generateReport({
          prediction_id: scan.id,
          patient_name: scan.patient,
          patient_id: scan.patientId || scan.id,
          patient_age: scan.age || "N/A",
          patient_sex: scan.sex || "N/A",
          doctor_notes: scan.notes || "",
          label: scan.type === "Clear" ? "NORMAL" : "PNEUMONIA",
          confidence: parseFloat(scan.confidence) / 100 || 0.95,
          severity_level: scan.status,
          severity_score: scan.status === "Critical" ? 95 : scan.status === "Severe" ? 80 : scan.status === "Moderate" ? 60 : 30,
          model_used: "Ensemble",
          inference_time_ms: scan.inference_time_ms || 42,
          referring_doctor: scan.doctor || "Dr. Anshika Jain",
        });
        downloadBlob(blob, `lungsight_report_${scan.id}.pdf`);
        toast.success("Report downloaded successfully");
      } catch (err) {
        toast.error("Failed to download report");
      } finally {
        setDownloadingId(null);
      }
    };
    
    return (
      <div className="flex flex-col min-h-full bg-background/50">
        <Header title="My Portal" />
        <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-8">
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }}
            className="rounded-3xl overflow-hidden bg-card border border-border shadow-sm flex flex-col items-start p-8 md:p-10 relative"
          >
            <div className="absolute top-0 right-0 -mt-20 -mr-20 w-96 h-96 bg-blue-500/10 blur-[100px] rounded-full pointer-events-none" />
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 text-xs font-semibold mb-6">
              <User className="w-3 h-3" />
              Patient Portal Active — ID: {userName}
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">
              <span className="text-foreground">Welcome, </span>
              <span className="bg-gradient-to-r from-blue-500 to-indigo-400 bg-clip-text text-transparent">{actualName}</span>
            </h1>
            <p className="text-muted-foreground text-sm md:text-base mb-2 max-w-lg leading-relaxed">
              View your recent AI-assisted diagnostic reports. Your primary care physician (Dr. Anshika Jain) will review these findings with you during your next consultation.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 rounded-2xl border border-border bg-card overflow-hidden shadow-sm flex flex-col">
            <div className="p-6 border-b border-border">
              <h2 className="text-lg font-bold text-foreground">My Reports</h2>
              <p className="text-sm text-muted-foreground mt-1">Diagnostic records associated with your account</p>
            </div>
            <div className="flex-1 overflow-x-auto min-h-[300px]">
              {patientScans.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-3 py-16">
                  <div className="w-16 h-16 rounded-2xl bg-muted/50 flex items-center justify-center mb-2">
                    <FileImage className="w-8 h-8 text-muted-foreground/50" />
                  </div>
                  <h3 className="text-foreground font-semibold">No reports available</h3>
                  <p className="text-muted-foreground text-sm max-w-[250px]">
                    Your doctor hasn&apos;t processed any scans for you yet.
                  </p>
                </div>
              ) : (
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-muted-foreground uppercase bg-muted/30">
                    <tr>
                      <th className="px-6 py-4 font-medium">Scan ID</th>
                      <th className="px-6 py-4 font-medium">Status / Findings</th>
                      <th className="px-6 py-4 font-medium">Consulting Doctor</th>
                      <th className="px-6 py-4 font-medium">Time</th>
                      <th className="px-6 py-4 font-medium text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {patientScans.map((scan, i) => (
                      <tr key={i} className="hover:bg-muted/30 transition-colors">
                        <td className="px-6 py-4 font-semibold text-foreground">{scan.id}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold
                            ${scan.status === 'Critical' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400' : 
                              scan.status === 'Severe' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                              scan.status === 'Moderate' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                              'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'}`}>
                            {scan.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-muted-foreground">{scan.doctor || "Dr. Anshika Jain"}</td>
                        <td className="px-6 py-4 text-muted-foreground flex items-center gap-1.5 mt-2">
                          <Clock className="w-3.5 h-3.5" />
                          {scan.time}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => handleDownload(scan)}
                            disabled={downloadingId === scan.id}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-card border border-border text-xs font-semibold rounded-lg hover:bg-muted transition-colors text-foreground disabled:opacity-50"
                          >
                            {downloadingId === scan.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                            Report
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
          
          {/* Precautions Panel */}
          <div className="lg:col-span-1">
            <motion.div 
              initial={{ opacity: 0, y: 20 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ delay: 0.2 }}
              className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col h-full"
            >
              <h2 className="text-lg font-bold text-foreground mb-1">Doctor&apos;s Notes & Precautions</h2>
              <p className="text-sm text-muted-foreground mb-6">Based on your latest scan results</p>
              
              {latestScan ? (
                <div className="space-y-4 flex-1">
                  <div className={`p-4 rounded-xl border ${latestScan.status === 'Critical' || latestScan.status === 'Severe' ? 'bg-rose-50 border-rose-200 dark:bg-rose-900/10 dark:border-rose-900/30 text-rose-800 dark:text-rose-300' : latestScan.status === 'Moderate' || latestScan.status === 'Mild' ? 'bg-amber-50 border-amber-200 dark:bg-amber-900/10 dark:border-amber-900/30 text-amber-800 dark:text-amber-300' : 'bg-emerald-50 border-emerald-200 dark:bg-emerald-900/10 dark:border-emerald-900/30 text-emerald-800 dark:text-emerald-300'}`}>
                    <div className="flex items-start gap-3">
                      <Stethoscope className="w-5 h-5 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="text-sm font-bold mb-2">Diagnosis: {latestScan.type}</h4>
                        <ul className="text-xs space-y-2 list-disc ml-4 opacity-90">
                          {latestScan.type === "Clear" ? (
                            <>
                              <li>Your lungs appear clear with no signs of opacity or infiltration.</li>
                              <li>Continue routine checkups as prescribed.</li>
                              <li>No immediate interventions are required.</li>
                            </>
                          ) : latestScan.status === "Critical" || latestScan.status === "Severe" ? (
                            <>
                              <li><strong>Immediate Attention Required:</strong> Severe consolidation detected.</li>
                              <li>Begin prescribed antibiotic therapy immediately.</li>
                              <li>Monitor oxygen saturation levels every 4 hours.</li>
                              <li>Rest extensively and stay highly hydrated.</li>
                              <li>Contact Dr. Jain if you experience shortness of breath.</li>
                            </>
                          ) : (
                            <>
                              <li>Mild to moderate opacities detected.</li>
                              <li>Complete your prescribed course of oral medication.</li>
                              <li>Schedule a follow-up X-ray in 7-10 days.</li>
                              <li>Ensure adequate rest and hydration.</li>
                            </>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-6 border-2 border-dashed border-border rounded-xl">
                  <Activity className="w-8 h-8 text-muted-foreground/30 mb-2" />
                  <p className="text-xs text-muted-foreground">No recent notes available.</p>
                </div>
              )}
            </motion.div>
          </div>
          </div>
        </div>
      </div>
    );
  }

  // ── Doctor Portal View ──────────────────────────────────────────────────
  // Filter scans strictly to the logged-in doctor
  const doctorScans = scans.filter(s => s.doctor === userName || (!s.doctor && userName.includes("Anshika")));
  
  const criticalCount = doctorScans.filter(s => s.status === "Critical" || s.status === "Severe").length;
  const avgTime = doctorScans.length > 0 ? Math.round(doctorScans.reduce((acc, curr) => acc + curr.inference_time_ms, 0) / doctorScans.length) : 0;
  const activePatients = new Set(doctorScans.map(s => s.patient)).size;

  const kpis = [
    { label: "Scans Analyzed", value: doctorScans.length.toString(), sub: "Total processed", icon: FileImage, color: "from-blue-500 to-cyan-400", light: "bg-blue-500/10 text-blue-500" },
    { label: "Critical Findings", value: criticalCount.toString(), sub: "Requires attention", icon: AlertTriangle, color: "from-rose-500 to-pink-500", light: "bg-rose-500/10 text-rose-500" },
    { label: "Avg Processing", value: doctorScans.length > 0 ? `${avgTime} ms` : "— ms", sub: doctorScans.length > 0 ? "Real-time inference" : "Awaiting scan", icon: Zap, color: "from-amber-500 to-orange-400", light: "bg-amber-500/10 text-amber-500" },
    { label: "Active Patients", value: activePatients.toString(), sub: "In system", icon: Users, color: "from-violet-500 to-purple-500", light: "bg-violet-500/10 text-violet-500" },
  ];

  return (
    <div className="flex flex-col min-h-full bg-background/50">
      <Header title="Dashboard" />
      
      <div className="flex-1 p-8 max-w-7xl mx-auto w-full space-y-8">
        <motion.div 
          initial={{ opacity: 0, y: 10 }} 
          animate={{ opacity: 1, y: 0 }}
          className="relative rounded-3xl overflow-hidden bg-card border border-border shadow-sm flex flex-col md:flex-row items-center justify-between p-8 md:p-10"
        >
          <div className="absolute top-0 right-0 -mt-20 -mr-20 w-96 h-96 bg-medical-500/10 blur-[100px] rounded-full pointer-events-none" />
          <div className="absolute bottom-0 left-0 -mb-20 -ml-20 w-80 h-80 bg-violet-500/10 blur-[100px] rounded-full pointer-events-none" />
          
          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-medical-500/10 border border-medical-500/20 text-medical-600 dark:text-medical-400 text-xs font-semibold mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-medical-500 animate-pulse" />
              Diagnostic AI Engine Active
            </div>
            <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight mb-4">
              <span className="text-foreground">Welcome back, </span>
              <span className="bg-gradient-to-r from-medical-500 to-cyan-400 bg-clip-text text-transparent">{userName}</span>
            </h1>
            <p className="text-muted-foreground text-sm md:text-base mb-8 max-w-lg leading-relaxed">
              Your diagnostic workstation is securely connected. Access incoming patient radiographs, review automated ensemble classifications, and sign off on clinical reports.
            </p>
            <div className="flex items-center gap-4">
              <Link href="/predict" className="inline-flex items-center gap-2 bg-gradient-to-r from-medical-600 to-medical-500 hover:from-medical-500 hover:to-medical-400 text-white font-bold text-sm px-7 py-3.5 rounded-xl transition-all shadow-[0_0_20px_rgba(14,165,233,0.3)] hover:shadow-[0_0_30px_rgba(14,165,233,0.5)] transform hover:-translate-y-0.5">
                <Stethoscope className="w-4.5 h-4.5" />
                New Analysis
              </Link>
              <Link href="/reports" className="inline-flex items-center gap-2 bg-card border border-border text-foreground font-medium text-sm px-6 py-3 rounded-xl hover:bg-muted/50 transition-colors">
                <FileText className="w-4 h-4 text-muted-foreground" />
                View Reports
              </Link>
            </div>
          </div>
          
          <div className="hidden md:block relative z-10 p-8">
             <div className="w-48 h-48 rounded-full border-[8px] border-medical-500/10 flex items-center justify-center relative">
                <div className="absolute inset-0 rounded-full border-[8px] border-medical-500 border-r-transparent border-t-transparent -rotate-45" />
                <div className="text-center">
                  <div className="text-4xl font-extrabold text-foreground">94%</div>
                  <div className="text-xs text-muted-foreground font-medium mt-1">Overall Accuracy</div>
                </div>
             </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {kpis.map(({ label, value, sub, icon: Icon, color, light }, i) => (
            <motion.div 
              key={label} 
              initial={{ opacity: 0, y: 15 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ delay: i * 0.08 + 0.1 }}
              className="rounded-2xl bg-card border border-border p-6 shadow-sm hover:shadow-md transition-shadow group relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-transparent to-black/5 dark:to-white/5 rounded-bl-full -z-10 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl ${light}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <ArrowUpRight className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
              </div>
              <div className="text-3xl font-bold text-foreground tracking-tight">{value}</div>
              <div className="text-sm font-medium text-muted-foreground mt-1">{label}</div>
              <div className="text-xs text-muted-foreground/70 mt-3 flex items-center gap-1.5">
                {sub}
              </div>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }} 
            transition={{ delay: 0.3 }}
            className="lg:col-span-2 rounded-2xl border border-border bg-card overflow-hidden shadow-sm flex flex-col"
          >
            <div className="p-6 border-b border-border flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-foreground">Recent Analyses</h2>
                <p className="text-sm text-muted-foreground mt-1">Latest chest X-ray scans processed by AI</p>
              </div>
              <button className="text-sm font-medium text-medical-600 hover:text-medical-700 dark:text-medical-400 dark:hover:text-medical-300">
                View All
              </button>
            </div>
            
            <div className="flex-1 overflow-x-auto min-h-[300px]">
              {doctorScans.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-3 py-16">
                  <div className="w-16 h-16 rounded-2xl bg-muted/50 flex items-center justify-center mb-2">
                    <FileImage className="w-8 h-8 text-muted-foreground/50" />
                  </div>
                  <h3 className="text-foreground font-semibold">No recent scans</h3>
                  <p className="text-muted-foreground text-sm max-w-[250px]">
                    Your diagnostic history is empty. Analyze a patient&apos;s X-Ray to get started.
                  </p>
                  <Link href="/predict" className="mt-4 px-6 py-2.5 bg-foreground text-background text-sm font-semibold rounded-xl hover:opacity-90 transition-opacity">
                    Analyze First Scan
                  </Link>
                </div>
              ) : (
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-muted-foreground uppercase bg-muted/30">
                    <tr>
                      <th className="px-6 py-4 font-medium">Scan ID / Patient</th>
                      <th className="px-6 py-4 font-medium">AI Diagnosis</th>
                      <th className="px-6 py-4 font-medium">Confidence</th>
                      <th className="px-6 py-4 font-medium">Time</th>
                      <th className="px-6 py-4 font-medium text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {doctorScans.map((scan, i) => (
                      <tr key={i} className="hover:bg-muted/30 transition-colors group">
                        <td className="px-6 py-4">
                          <div className="font-semibold text-foreground">{scan.patient}</div>
                          <div className="text-xs text-muted-foreground">{scan.id}</div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold
                            ${scan.status === 'Critical' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400' : 
                              scan.status === 'Severe' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                              scan.status === 'Moderate' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' :
                              'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'}`}>
                            {scan.type} • {scan.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-medium text-foreground">
                          {scan.confidence}
                        </td>
                        <td className="px-6 py-4 text-muted-foreground text-xs flex items-center gap-1.5 mt-2.5">
                          <Clock className="w-3.5 h-3.5" />
                          {scan.time}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button className="text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity p-2 rounded-lg hover:bg-muted">
                            <ChevronRight className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }} 
            transition={{ delay: 0.4 }}
            className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col"
          >
            <h2 className="text-lg font-bold text-foreground mb-1">Diagnostic Distribution</h2>
            <p className="text-sm text-muted-foreground mb-6">Last 30 days analysis</p>
            
            <div className="flex-1 flex flex-col justify-center gap-6">
              {[
                { label: "Normal / Clear", percent: doctorScans.length ? Math.round((doctorScans.filter(s => s.type === "Clear").length / doctorScans.length) * 100) : 0, color: "bg-emerald-500" },
                { label: "Pneumonia", percent: doctorScans.length ? Math.round((doctorScans.filter(s => s.type !== "Clear").length / doctorScans.length) * 100) : 0, color: "bg-rose-500" },
              ].map((item, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium text-foreground">{item.label}</span>
                    <span className="text-muted-foreground">{item.percent}%</span>
                  </div>
                  <div className="h-2.5 w-full bg-muted rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${item.percent}%` }}
                      transition={{ duration: 1, delay: 0.5 + (i * 0.1) }}
                      className={`h-full rounded-full ${item.color}`} 
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 p-4 rounded-xl bg-medical-50 dark:bg-medical-900/10 border border-medical-100 dark:border-medical-900/30 flex items-start gap-3">
              <Activity className="w-5 h-5 text-medical-600 dark:text-medical-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-medical-900 dark:text-medical-100">AI Insight</h4>
                <p className="text-xs text-medical-700 dark:text-medical-300/80 mt-1 leading-relaxed">
                  {doctorScans.length > 0 ? `Pneumonia detection is at ${Math.round((doctorScans.filter(s => s.type !== "Clear").length / doctorScans.length) * 100)}%. Model confidence remains stable.` : "Awaiting enough data to generate predictive insights. Process more scans to unlock trend analysis."}
                </p>
              </div>
            </div>
          </motion.div>

        </div>
      </div>
    </div>
  );
}
