"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Stethoscope, User, ArrowRight, Wind, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [role, setRole] = useState<"doctor" | "patient">("doctor");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate login and store user identity
    if (role === "doctor") {
      const name = email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      localStorage.setItem("ls_user_name", name.toLowerCase().startsWith("dr") ? name : `Dr. ${name}`);
    } else {
      localStorage.setItem("ls_user_name", email.trim().toUpperCase()); // Store Patient ID
    }
    localStorage.setItem("ls_user_role", role);
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen bg-grid-pattern flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-transparent via-background/80 to-background pointer-events-none" />
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-medical-500/20 blur-[120px] animate-pulse-slow mix-blend-screen pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 h-96 w-96 rounded-full bg-violet-500/20 blur-[120px] animate-pulse-slow mix-blend-screen pointer-events-none" style={{ animationDelay: '2s' }} />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-medical-500 to-medical-700 shadow-xl mb-4">
            <Wind className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">LungSight AI</h1>
          <p className="text-muted-foreground text-sm mt-1">Secure Medical Portal</p>
        </div>

        {/* Login Card */}
        <div className="glass-panel rounded-3xl p-8 border border-white/10 shadow-2xl">
          {/* Role Toggle */}
          <div className="flex p-1 bg-muted/50 rounded-xl mb-8">
            <button
              onClick={() => setRole("doctor")}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-semibold rounded-lg transition-all ${
                role === "doctor" 
                  ? "bg-white dark:bg-slate-800 text-foreground shadow-sm" 
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Stethoscope className="w-4 h-4" />
              Clinician
            </button>
            <button
              onClick={() => setRole("patient")}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-semibold rounded-lg transition-all ${
                role === "patient" 
                  ? "bg-white dark:bg-slate-800 text-foreground shadow-sm" 
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <User className="w-4 h-4" />
              Patient
            </button>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                {role === "doctor" ? "Medical Email" : "Patient ID (e.g. ACC-8921-X)"}
              </label>
              <input 
                type={role === "doctor" ? "email" : "text"}
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-background/50 border border-border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-medical-500 focus:border-transparent transition-all"
                placeholder={role === "doctor" ? "dr.anshika@lungsight.ai" : "ACC-8921-X"}
              />
            </div>
            
            <div>
              <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Password
              </label>
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-background/50 border border-border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-medical-500 focus:border-transparent transition-all"
                placeholder="••••••••"
              />
            </div>

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="rounded border-border text-medical-500 focus:ring-medical-500" />
                <span className="text-muted-foreground">Remember me</span>
              </label>
              <a href="#" className="text-medical-600 dark:text-medical-400 font-semibold hover:underline">
                Forgot password?
              </a>
            </div>

            <button 
              type="submit"
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-medical-600 to-medical-500 hover:from-medical-700 hover:to-medical-600 text-white rounded-xl py-3.5 font-bold shadow-lg transition-all"
            >
              Secure Login <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-8 flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>HIPAA Compliant & End-to-End Encrypted</span>
          </div>
        </div>

        <div className="mt-8 text-center text-xs text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/" className="text-medical-600 dark:text-medical-400 font-semibold hover:underline">
            Contact Administration
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
