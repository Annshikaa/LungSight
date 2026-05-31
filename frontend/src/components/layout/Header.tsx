"use client";

import { Bell, Moon, Search, Sun, X, LogOut } from "lucide-react";
import { useEffect, useRef, useState } from "react";

const NOTIFICATIONS = [
  { id: 1, title: "Analysis Complete", message: "DenseNet121 processed your X-ray in 131ms.", time: "2m ago", read: false },
  { id: 2, title: "Model Loaded", message: "All 3 ensemble models are active and ready.", time: "5m ago", read: false },
  { id: 3, title: "Report Generated", message: "PDF report has been downloaded successfully.", time: "12m ago", read: true },
  { id: 4, title: "High Confidence Result", message: "Ensemble achieved 96.8% model agreement.", time: "1h ago", read: true },
];

export function Header({ title }: { title: string }) {
  const [dark, setDark] = useState(false);
  const [showNotifs, setShowNotifs] = useState(false);
  const [notifs, setNotifs] = useState(NOTIFICATIONS);
  const [role, setRole] = useState("doctor");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const savedRole = localStorage.getItem("ls_user_role");
    if (savedRole) setRole(savedRole);
    
    const saved = localStorage.getItem("ls_theme");
    if (saved === "dark") {
      setDark(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setShowNotifs(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const toggleDark = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("ls_theme", next ? "dark" : "light");
  };

  const unread = notifs.filter((n) => !n.read).length;

  const markAllRead = () => setNotifs((prev) => prev.map((n) => ({ ...n, read: true })));
  const dismiss = (id: number) => setNotifs((prev) => prev.filter((n) => n.id !== id));

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-card px-6">
      <h2 className="text-lg font-semibold text-foreground">{title}</h2>

      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative hidden md:flex items-center">
          <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search scans…"
            className="h-9 rounded-lg border border-border bg-muted pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-medical-500"
          />
        </div>

        {/* Notifications */}
        <div className="relative" ref={ref}>
          <button
            onClick={() => setShowNotifs((v) => !v)}
            className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-muted hover:bg-accent transition-colors"
          >
            <Bell className="h-4 w-4 text-muted-foreground" />
            {unread > 0 && (
              <span className="absolute right-1.5 top-1.5 flex h-2 w-2 items-center justify-center rounded-full bg-red-500" />
            )}
          </button>

          {showNotifs && (
            <div className="absolute right-0 top-11 z-50 w-80 rounded-xl border border-border bg-card shadow-xl">
              <div className="flex items-center justify-between border-b border-border px-4 py-3">
                <span className="text-sm font-bold text-foreground">
                  Notifications {unread > 0 && <span className="ml-1 rounded-full bg-red-100 px-1.5 py-0.5 text-xs text-red-700">{unread}</span>}
                </span>
                {unread > 0 && (
                  <button onClick={markAllRead} className="text-xs text-medical-500 hover:underline">
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-72 overflow-y-auto divide-y divide-border">
                {notifs.length === 0 ? (
                  <p className="px-4 py-6 text-center text-sm text-muted-foreground">No notifications</p>
                ) : notifs.map((n) => (
                  <div key={n.id} className={`flex gap-3 px-4 py-3 hover:bg-muted/50 transition-colors ${!n.read ? "bg-medical-50 dark:bg-medical-900/10" : ""}`}>
                    <div className={`mt-1.5 h-2 w-2 flex-shrink-0 rounded-full ${!n.read ? "bg-medical-500" : "bg-transparent"}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-foreground">{n.title}</p>
                      <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{n.message}</p>
                      <p className="text-[10px] text-muted-foreground mt-1">{n.time}</p>
                    </div>
                    <button onClick={() => dismiss(n.id)} className="mt-1 text-muted-foreground hover:text-foreground">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Dark mode */}
        <button
          onClick={toggleDark}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-muted hover:bg-accent transition-colors"
          aria-label="Toggle dark mode"
        >
          {dark ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-muted-foreground" />}
        </button>

        {/* Avatar & Logout */}
        <div className="flex items-center gap-2 border-l border-border pl-3 ml-1">
          <div className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold text-white shadow-sm ${role === 'patient' ? 'bg-blue-600' : 'gradient-medical'}`}>
            {role === 'patient' ? 'Pt' : 'Dr'}
          </div>
          <button
            onClick={() => {
              localStorage.removeItem("ls_user_name");
              localStorage.removeItem("ls_user_role");
              window.location.href = "/login";
            }}
            title="Secure Logout"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
