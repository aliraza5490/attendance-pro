"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CalendarCheck2,
  Users,
  Radio,
  Building2,
  Sparkles,
  Server,
} from "lucide-react";
import { api } from "@/lib/api";

const navItems = [
  {
    label: "Overview",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Attendance Records",
    href: "/attendance",
    icon: CalendarCheck2,
  },
  {
    label: "Employee Directory",
    href: "/employees",
    icon: Users,
  },
  {
    label: "Live Monitor HUD",
    href: "/live",
    icon: Radio,
    badge: "LIVE",
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await api.getHealth();
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="w-72 bg-[#0d1322]/90 backdrop-blur-xl border-r border-slate-800/80 flex flex-col h-screen sticky top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800/60">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-cyan-600 via-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-cyan-500/20 ring-1 ring-white/20">
            <Building2 className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold tracking-tight text-white text-lg">
                Vision<span className="text-cyan-400">Attend</span>
              </span>
              <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">
              Employee & Faculty Presence
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold tracking-wider text-slate-400 uppercase">
          Workplace Management
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href ||
            (item.href === "/employees" && pathname === "/students");

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
                isActive
                  ? "bg-gradient-to-r from-cyan-500/15 to-indigo-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-500/10"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive
                      ? "text-cyan-400"
                      : "text-slate-400 group-hover:text-slate-300"
                  }`}
                />
                <span>{item.label}</span>
              </div>

              {item.badge && (
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500/30 animate-pulse">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Backend Status & System Info */}
      <div className="p-4 border-t border-slate-800/60 bg-slate-950/40 m-3 rounded-2xl border">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <Server className="w-3.5 h-3.5 text-cyan-400" />
            <span>FastAPI Backend</span>
          </div>
          <span
            className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
              backendOnline === true
                ? "bg-emerald-950 text-emerald-300 border border-emerald-500/30"
                : backendOnline === false
                ? "bg-rose-950 text-rose-300 border border-rose-500/30"
                : "bg-amber-950 text-amber-300 border border-amber-500/30"
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                backendOnline === true
                  ? "bg-emerald-400 animate-ping"
                  : backendOnline === false
                  ? "bg-rose-400"
                  : "bg-amber-400"
              }`}
            />
            {backendOnline === true
              ? "ONLINE"
              : backendOnline === false
              ? "OFFLINE"
              : "CONNECTING"}
          </span>
        </div>
        <p className="text-[11px] text-slate-400 leading-tight">
          Face + MediaPipe Gesture HUD Engine active on port 8000.
        </p>
      </div>
    </aside>
  );
}
