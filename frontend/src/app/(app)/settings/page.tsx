"use client";

import { useEffect, useState } from "react";
import { Info, Save, User, Shield, Bell, Monitor } from "lucide-react";
import toast from "react-hot-toast";
import { Header } from "@/components/layout/Header";
import { getHealth } from "@/lib/api";

const ROLES = ["Researcher", "Doctor", "Radiologist", "Admin"];

export default function SettingsPage() {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [activeTab, setActiveTab] = useState<"profile" | "system" | "notifications">("profile");

  const [profile, setProfile] = useState({
    full_name: "Dr. Anshika Jain",
    email: "anshika@lungsight.ai",
    username: "dr_anshika",
    role: "Researcher",
    hospital: "LungSight Medical Center",
    bio: "AI/ML researcher specializing in medical imaging and explainable AI.",
  });

  const [notifSettings, setNotifSettings] = useState({
    analysis_complete: true,
    high_severity: true,
    model_updates: false,
    weekly_report: true,
  });

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth({ status: "offline" }));
    const saved = localStorage.getItem("ls_profile");
    if (saved) {
      setProfile(JSON.parse(saved));
    } else {
      const name = localStorage.getItem("ls_user_name") || "Dr. Anshika Jain";
      const role = localStorage.getItem("ls_user_role") || "doctor";
      setProfile((p) => ({
        ...p,
        full_name: name,
        username: name.toLowerCase().replace(/[^a-z0-9]/g, "_"),
        role: role === "patient" ? "Patient" : "Researcher",
        hospital: role === "patient" ? "N/A" : "LungSight Medical Center",
        bio: role === "patient" ? "Patient account" : "AI/ML researcher specializing in medical imaging and explainable AI.",
      }));
    }
  }, []);

  const saveProfile = () => {
    localStorage.setItem("ls_profile", JSON.stringify(profile));
    localStorage.setItem("ls_user_name", profile.full_name);
    toast.success("Profile saved!");
  };

  const tabs = profile.role === "Patient" 
    ? [{ id: "profile", label: "Profile", icon: User }] as const
    : [
        { id: "profile", label: "Profile", icon: User },
        { id: "system", label: "System", icon: Monitor },
        { id: "notifications", label: "Notifications", icon: Bell },
      ] as const;

  return (
    <div className="flex flex-col min-h-full">
      <Header title="Settings" />
      <div className="flex-1 p-6">
        <div className="max-w-3xl mx-auto space-y-6">

          {/* Tabs */}
          <div className="flex gap-1 rounded-xl border border-border bg-muted p-1">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 flex-1 justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors
                  ${activeTab === id ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>

          {/* Profile Tab */}
          {activeTab === "profile" && (
            <div className="space-y-4">
              {/* Avatar */}
              <div className="rounded-2xl border border-border bg-card p-6">
                <div className="flex items-center gap-5">
                  <div className="flex h-20 w-20 items-center justify-center rounded-full gradient-medical text-3xl font-bold text-white flex-shrink-0">
                    {profile.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-foreground">{profile.full_name}</h3>
                    <p className="text-sm text-muted-foreground">{profile.role} {profile.hospital !== "N/A" ? `· ${profile.hospital}` : ""}</p>
                    {profile.role !== "Patient" && (
                      <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-medical-100 dark:bg-medical-900/40 px-2.5 py-0.5 text-xs font-semibold text-medical-700 dark:text-medical-300">
                        <Shield className="h-3 w-3" /> Verified Researcher
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Form */}
              <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
                <h3 className="text-sm font-bold text-foreground">Personal Information</h3>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Full Name</label>
                    <input
                      value={profile.full_name}
                      onChange={(e) => setProfile((p) => ({ ...p, full_name: e.target.value }))}
                      className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Username</label>
                    <input
                      value={profile.username}
                      onChange={(e) => setProfile((p) => ({ ...p, username: e.target.value }))}
                      className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Email</label>
                  <input
                    value={profile.email}
                    onChange={(e) => setProfile((p) => ({ ...p, email: e.target.value }))}
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Role</label>
                    <select
                      value={profile.role}
                      onChange={(e) => setProfile((p) => ({ ...p, role: e.target.value }))}
                      className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500"
                    >
                      {ROLES.map((r) => <option key={r}>{r}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Hospital / Institution</label>
                    <input
                      value={profile.hospital}
                      onChange={(e) => setProfile((p) => ({ ...p, hospital: e.target.value }))}
                      className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Bio</label>
                  <textarea
                    value={profile.bio}
                    onChange={(e) => setProfile((p) => ({ ...p, bio: e.target.value }))}
                    rows={3}
                    className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-medical-500 resize-none"
                  />
                </div>

                <button
                  onClick={saveProfile}
                  className="flex items-center gap-2 rounded-xl gradient-medical px-5 py-2.5 text-sm font-bold text-white hover:opacity-90 transition"
                >
                  <Save className="h-4 w-4" /> Save Profile
                </button>
              </div>
            </div>
          )}

          {/* System Tab */}
          {activeTab === "system" && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-border bg-card p-6">
                <h3 className="text-sm font-bold text-foreground mb-4">System Status</h3>
                <div className="space-y-3">
                  {[
                    { label: "Backend API",         status: health?.status === "healthy" },
                    { label: "AI Models",           status: true },
                    { label: "Lung Segmentation",   status: true },
                    { label: "Explainability XAI",  status: true },
                    { label: "Report Generator",    status: true },
                  ].map(({ label, status }) => (
                    <div key={label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                      <span className="text-sm text-foreground">{label}</span>
                      <div className="flex items-center gap-2">
                        <div className={`h-2 w-2 rounded-full ${status ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
                        <span className={`text-xs font-medium ${status ? "text-green-600" : "text-red-600"}`}>
                          {status ? "Online" : "Offline"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-medical-200 bg-medical-50 dark:bg-medical-900/20 p-6">
                <div className="flex gap-3">
                  <Info className="h-5 w-5 text-medical-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-bold text-foreground mb-2">About LungSight AI</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      LungSight AI v1.0 — Research-grade explainable pneumonia detection platform.
                    </p>
                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                      <span><strong>Backend:</strong> FastAPI 0.115</span>
                      <span><strong>Frontend:</strong> Next.js 15</span>
                      <span><strong>ML:</strong> PyTorch 2.5</span>
                      <span><strong>Accuracy:</strong> 93.4% (DenseNet121)</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-amber-200 bg-amber-50 dark:bg-amber-900/20 p-5">
                <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
                  <strong>Medical Disclaimer:</strong> LungSight AI is a research tool and is NOT a certified medical device.
                  All AI-generated findings must be reviewed by a licensed radiologist or physician before clinical use.
                </p>
              </div>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === "notifications" && (
            <div className="rounded-2xl border border-border bg-card p-6 space-y-4">
              <h3 className="text-sm font-bold text-foreground">Notification Preferences</h3>
              {[
                { key: "analysis_complete", label: "Analysis Complete", desc: "When an X-ray analysis finishes" },
                { key: "high_severity", label: "High Severity Alert", desc: "When a Severe or Critical case is detected" },
                { key: "model_updates", label: "Model Updates", desc: "When new model weights are available" },
                { key: "weekly_report", label: "Weekly Summary", desc: "Weekly digest of scan statistics" },
              ].map(({ key, label, desc }) => (
                <div key={key} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                  <div>
                    <p className="text-sm font-medium text-foreground">{label}</p>
                    <p className="text-xs text-muted-foreground">{desc}</p>
                  </div>
                  <button
                    onClick={() => setNotifSettings((p) => ({ ...p, [key]: !p[key as keyof typeof p] }))}
                    className={`relative h-6 w-11 rounded-full transition-colors ${notifSettings[key as keyof typeof notifSettings] ? "bg-medical-500" : "bg-muted"}`}
                  >
                    <div className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${notifSettings[key as keyof typeof notifSettings] ? "translate-x-5" : "translate-x-0.5"}`} />
                  </button>
                </div>
              ))}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
