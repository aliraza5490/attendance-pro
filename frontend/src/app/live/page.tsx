"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Radio,
  LogIn,
  LogOut,
  Camera,
  Activity,
  Terminal,
  Building,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ManualCheckInModal } from "@/components/ManualCheckInModal";
import { AddEmployeeModal } from "@/components/AddEmployeeModal";
import { api, ActivityLog, SummaryMetrics } from "@/lib/api";

export default function LiveMonitorPage() {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [summary, setSummary] = useState<SummaryMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [pollingActive, setPollingActive] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Modals
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [addEmployeeModalOpen, setAddEmployeeModalOpen] = useState(false);

  const fetchLiveData = useCallback(async () => {
    try {
      const [fetchedLogs, sum] = await Promise.all([
        api.getLogs({ limit: 15 }),
        api.getSummary(),
      ]);
      setLogs(fetchedLogs);
      setSummary(sum);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Live monitor fetch error", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLiveData();
    if (!pollingActive) return;
    const interval = setInterval(fetchLiveData, 2000); // 2-second live poll
    return () => clearInterval(interval);
  }, [fetchLiveData, pollingActive]);

  return (
    <div className="flex-1 flex flex-col">
      <Navbar
        title="Live Office Monitor & HUD Stream"
        subtitle="Real-time employee recognition and gesture activity"
        onRefresh={fetchLiveData}
        onOpenManualModal={() => setManualModalOpen(true)}
        onOpenAddEmployeeModal={() => setAddEmployeeModalOpen(true)}
      />

      <main className="p-8 space-y-8 max-w-7xl mx-auto w-full">
        {/* Stream Banner & Status */}
        <div className="glass-panel rounded-2xl p-6 relative overflow-hidden border border-cyan-500/20">
          <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-wrap items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-14 h-14 rounded-2xl bg-slate-900 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-lg shadow-cyan-500/20">
                  <Radio className="w-7 h-7 animate-pulse" />
                </div>
                <span className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-[#0b0f19] animate-pulse-glow" />
              </div>
              <div>
                <div className="flex items-center gap-2.5">
                  <h3 className="text-lg font-bold text-white">Real-Time Biometric Stream</h3>
                  <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                    LIVE
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Auto-syncing every 2s • Last ping: {lastUpdated.toLocaleTimeString()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Quick stats on live banner */}
              <div className="hidden sm:flex items-center gap-6 px-5 py-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
                <div className="text-center">
                  <div className="text-xs text-slate-400 font-medium">Present Today</div>
                  <div className="text-base font-mono font-bold text-emerald-400">
                    {summary?.present_today ?? "--"}
                  </div>
                </div>
                <div className="h-7 w-[1px] bg-slate-800" />
                <div className="text-center">
                  <div className="text-xs text-slate-400 font-medium">In Office Now</div>
                  <div className="text-base font-mono font-bold text-cyan-400">
                    {summary?.checked_in_now ?? "--"}
                  </div>
                </div>
              </div>

              <button
                onClick={() => setPollingActive(!pollingActive)}
                className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition ${
                  pollingActive
                    ? "bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700"
                    : "bg-emerald-600 text-white border-emerald-500 hover:bg-emerald-500"
                }`}
              >
                {pollingActive ? "Pause Stream" : "Resume Stream"}
              </button>
            </div>
          </div>
        </div>

        {/* Gesture HUD Reference & Tracker Launch */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Gesture 1: Victory (Check-In) */}
          <div className="glass-panel rounded-2xl p-6 relative border-emerald-500/20 hover:border-emerald-500/40 transition">
            <div className="flex items-center justify-between mb-3">
              <span className="text-3xl">✌️</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500/30">
                CHECK-IN
              </span>
            </div>
            <h4 className="text-sm font-bold text-emerald-300 mb-1">Victory / Peace Sign</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Show a clear ✌ sign facing the vision camera to record employee arrival timestamp with
              instant verification.
            </p>
          </div>

          {/* Gesture 2: Thumbs-Up (Check-Out) */}
          <div className="glass-panel rounded-2xl p-6 relative border-amber-500/20 hover:border-amber-500/40 transition">
            <div className="flex items-center justify-between mb-3">
              <span className="text-3xl">👍</span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-500/30">
                CHECK-OUT
              </span>
            </div>
            <h4 className="text-sm font-bold text-amber-300 mb-1">Thumbs Up Sign</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Raise a clear 👍 facing the camera to timestamp employee departure. Updates occupancy
              stats instantly.
            </p>
          </div>

          {/* CLI Run Tracker helper */}
          <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between border-indigo-500/20">
            <div>
              <div className="flex items-center gap-2 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-2">
                <Terminal className="w-4 h-4" /> Vision Tracker Command
              </div>
              <p className="text-xs text-slate-400 mb-3">
                To launch the real-time webcam recognition HUD on your workstation:
              </p>
              <div className="p-2.5 rounded-xl bg-slate-950/90 border border-slate-800 text-[11px] font-mono text-cyan-300 select-all">
                uv run --package attendance-tracker tracker
              </div>
            </div>
          </div>
        </div>

        {/* Live Event Stream Timeline */}
        <div className="glass-panel rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Live Audit Log Stream
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              Showing last {logs.length} events
            </span>
          </div>

          {loading ? (
            <div className="py-16 text-center text-slate-500 text-xs">
              Loading live event stream...
            </div>
          ) : logs.length === 0 ? (
            <div className="py-16 text-center text-slate-500 text-xs space-y-2">
              <Camera className="w-8 h-8 mx-auto text-slate-600" />
              <p>No activity events detected yet today.</p>
              <p className="text-slate-600">Start the tracker HUD and present a gesture to see events appear here in real time.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {logs.map((log, idx) => {
                const name = log.employee_name || log.student_name;
                const empId = log.employee_id || log.student_id;
                return (
                  <div
                    key={log.id}
                    className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
                      idx === 0
                        ? "bg-slate-900/90 border-cyan-500/40 shadow-lg shadow-cyan-950/40"
                        : "bg-slate-900/50 border-slate-800/80 hover:bg-slate-900/80"
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`p-2.5 rounded-xl ${
                          log.action === "CHECK_IN"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                            : "bg-amber-500/20 text-amber-400 border border-amber-500/40"
                        }`}
                      >
                        {log.action === "CHECK_IN" ? (
                          <LogIn className="w-5 h-5" />
                        ) : (
                          <LogOut className="w-5 h-5" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-100">{name}</span>
                          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                            Badge #{empId}
                          </span>
                          {idx === 0 && (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-500/30">
                              NEW
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          Action:{" "}
                          <strong
                            className={
                              log.action === "CHECK_IN" ? "text-emerald-300" : "text-amber-300"
                            }
                          >
                            {log.action === "CHECK_IN"
                              ? "Checked In via ✌ Victory Sign"
                              : "Checked Out via 👍 Thumbs Up"}
                          </strong>
                        </div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-xs font-mono font-bold text-cyan-300">{log.time}</div>
                      <div className="text-[11px] text-slate-500 font-mono">{log.date}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      <ManualCheckInModal
        isOpen={manualModalOpen}
        onClose={() => setManualModalOpen(false)}
        onSuccess={fetchLiveData}
      />

      <AddEmployeeModal
        isOpen={addEmployeeModalOpen}
        onClose={() => setAddEmployeeModalOpen(false)}
        onSuccess={fetchLiveData}
      />
    </div>
  );
}
