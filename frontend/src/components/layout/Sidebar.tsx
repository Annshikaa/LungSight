"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Activity,
  BarChart3,
  Brain,
  FileText,
  FlaskConical,
  LayoutDashboard,
  Microscope,
  Wind,
  Settings,
  Stethoscope,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard",    href: "/dashboard",  icon: LayoutDashboard },
  { name: "Predict",      href: "/predict",    icon: Stethoscope },
  { name: "Research",     href: "/research",   icon: FlaskConical },
  { name: "Benchmark",    href: "/benchmark",  icon: BarChart3 },
  { name: "Reports",      href: "/reports",    icon: FileText },
  { name: "Analytics",    href: "/analytics",  icon: Activity },
];

const bottomNav = [
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [role, setRole] = useState("doctor");

  useEffect(() => {
    setRole(localStorage.getItem("ls_user_role") || "doctor");
  }, []);

  const visibleNav = role === "patient"
    ? navigation.filter(n => n.name === "Dashboard")
    : navigation;

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-border bg-card">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-border px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl gradient-medical">
          <Wind className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-foreground">LungSight AI</h1>
          <p className="text-[10px] text-muted-foreground">v1.0 — Research Edition</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-3 py-4">
        <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Clinical Tools
        </p>
        {visibleNav.map((item) => {
          const Icon = item.icon;
          const active = pathname.startsWith(item.href);
          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                whileHover={{ x: 2 }}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-medical-100 text-medical-700 dark:bg-medical-900/40 dark:text-medical-300"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <Icon className={cn("h-4 w-4", active && "text-medical-600 dark:text-medical-400")} />
                {item.name}
                {active && (
                  <motion.div
                    layoutId="sidebar-indicator"
                    className="ml-auto h-1.5 w-1.5 rounded-full bg-medical-500"
                  />
                )}
              </motion.div>
            </Link>
          );
        })}

        <div className="mt-auto pt-4">
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            System
          </p>
          {bottomNav.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href}>
                <div className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors">
                  <Icon className="h-4 w-4" />
                  {item.name}
                </div>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="border-t border-border p-4">
        <div className="flex items-center gap-2 rounded-lg bg-medical-50 dark:bg-medical-900/20 p-3">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <div>
            <p className="text-[11px] font-medium text-foreground">AI Models Active</p>
            <p className="text-[10px] text-muted-foreground">All 4 models ready</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
