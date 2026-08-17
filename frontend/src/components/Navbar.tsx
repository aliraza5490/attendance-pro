"use client";

import React, { useEffect, useState } from "react";
import { Clock, UserPlus, Fingerprint, RefreshCw } from "lucide-react";

interface NavbarProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
  onOpenManualModal?: () => void;
  onOpenAddEmployeeModal?: () => void;
  onOpenAddStudentModal?: () => void; // backwards compat
}

export function Navbar({
  title,
  subtitle,
  onRefresh,
  onOpenManualModal,
  onOpenAddEmployeeModal,
  onOpenAddStudentModal,
}: NavbarProps) {
  const [timeStr, setTimeStr] = useState<string>("");
  const [dateStr, setDateStr] = useState<string>("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleAddEmployee = onOpenAddEmployeeModal || onOpenAddStudentModal;

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: true,
        })
      );
      setDateStr(
        now.toLocaleDateString("en-US", {
          weekday: "short",
          month: "short",
          day: "numeric",
          year: "numeric",
        })
      );
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleRefreshClick = () => {
    if (!onRefresh) return;
    setIsRefreshing(true);
    onRefresh();
    setTimeout(() => setIsRefreshing(false), 600);
  };

  return (
    <header className="h-20 border-b border-slate-800/80 px-8 flex items-center justify-between bg-[#0d1322]/50 backdrop-blur-md sticky top-0 z-20">
      {/* Title & Subtitle */}
      <div>
        <h1 className="text-xl font-bold text-slate-100 tracking-tight">{title}</h1>
        {subtitle && (
          <p className="text-xs text-slate-400 font-medium mt-0.5">{subtitle}</p>
        )}
      </div>

      {/* Right Action Bar */}
      <div className="flex items-center gap-4">
        {/* Live Clock HUD */}
        <div className="hidden md:flex items-center gap-3 px-4 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-300 font-mono shadow-inner">
          <Clock className="w-4 h-4 text-cyan-400 animate-pulse" />
          <div className="text-right">
            <div className="text-xs font-bold text-cyan-300 leading-none">{timeStr}</div>
            <div className="text-[10px] text-slate-400 leading-tight mt-0.5">{dateStr}</div>
          </div>
        </div>

        {/* Refresh Button */}
        {onRefresh && (
          <button
            onClick={handleRefreshClick}
            aria-label="Refresh data"
            className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-300 hover:text-cyan-400 hover:border-cyan-500/40 transition duration-150 group"
          >
            <RefreshCw
              className={`w-4 h-4 transition-transform duration-500 ${
                isRefreshing ? "animate-spin text-cyan-400" : "group-hover:rotate-180"
              }`}
            />
          </button>
        )}

        {/* Manual Check-In Button */}
        {onOpenManualModal && (
          <button
            onClick={onOpenManualModal}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-200 text-xs font-semibold shadow-md transition duration-150"
          >
            <Fingerprint className="w-4 h-4 text-cyan-400" />
            <span>Manual Check-In</span>
          </button>
        )}

        {/* Register Employee Button */}
        {handleAddEmployee && (
          <button
            onClick={handleAddEmployee}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-cyan-600/20 transition duration-150 active:scale-95"
          >
            <UserPlus className="w-4 h-4" />
            <span>Register Employee</span>
          </button>
        )}
      </div>
    </header>
  );
}
