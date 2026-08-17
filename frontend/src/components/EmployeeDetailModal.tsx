"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  User,
  Calendar,
  CheckCircle,
  Clock,
  LogIn,
  LogOut,
  TrendingUp,
} from "lucide-react";
import { api, EmployeeDetail } from "@/lib/api";

interface EmployeeDetailModalProps {
  employeeId: number | null;
  studentId?: number | null; // compat
  isOpen: boolean;
  onClose: () => void;
}

export function EmployeeDetailModal({
  employeeId,
  studentId,
  isOpen,
  onClose,
}: EmployeeDetailModalProps) {
  const activeId = employeeId ?? studentId ?? null;
  const [detail, setDetail] = useState<EmployeeDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && activeId !== null) {
      setLoading(true);
      setFetchError(null);
      api
        .getEmployeeDetail(activeId)
        .then((data) => {
          // Normalize history / records field
          const historyList = data.history || (data as any).records || [];
          setDetail({
            ...data,
            history: historyList,
          });
        })
        .catch((err) => {
          console.error("Failed to load employee detail", err);
          setFetchError(err.message || "Failed to load employee details");
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, activeId]);

  if (!isOpen || activeId === null) return null;

  const historyList: Array<{
    date: string;
    check_in_time: string | null;
    check_out_time: string | null;
    status: string | null;
  }> = detail?.history || (detail as any)?.records || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-panel w-full max-w-2xl rounded-2xl p-6 shadow-2xl border border-slate-700/80 max-h-[88vh] flex flex-col relative">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center font-bold text-lg text-white shadow-lg shadow-cyan-500/20">
              {detail ? detail.name.charAt(0).toUpperCase() : <User className="w-6 h-6" />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-100">
                  {detail ? detail.name : `Employee #${activeId}`}
                </h2>
                <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                  Badge ID #{activeId}
                </span>
              </div>
              <p className="text-xs text-slate-400">Office & Faculty Presence Profile</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        {loading ? (
          <div className="py-20 text-center text-slate-500 text-sm">
            Loading employee record...
          </div>
        ) : fetchError ? (
          <div className="text-center py-16 text-rose-400 text-sm space-y-2">
            <p className="font-semibold">Unable to connect to backend server.</p>
            <p className="text-xs text-slate-400">Make sure FastAPI is running on port 8000.</p>
          </div>
        ) : detail ? (
          <div className="flex-1 overflow-y-auto space-y-6 pt-6">
            {/* Quick Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> Total Days Present
                </div>
                <div className="text-2xl font-bold font-mono text-emerald-400">
                  {detail.total_attendances ?? 0}
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                  <TrendingUp className="w-3.5 h-3.5 text-cyan-400" /> Attendance Rate
                </div>
                <div className="text-2xl font-bold font-mono text-cyan-400">
                  {detail.attendance_rate ?? 0}%
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="text-xs text-slate-400 flex items-center gap-1.5 mb-1">
                  <Calendar className="w-3.5 h-3.5 text-indigo-400" /> Last Active Date
                </div>
                <div className="text-sm font-semibold font-mono text-slate-200 mt-1">
                  {detail.last_attended_date || "No activity yet"}
                </div>
              </div>
            </div>

            {/* Attendance History Timeline */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                <Clock className="w-3.5 h-3.5 text-cyan-400" /> Shift & Attendance Timeline
              </h3>

              {historyList.length === 0 ? (
                <div className="p-8 rounded-xl bg-slate-900/40 border border-slate-800 text-center text-xs text-slate-500">
                  No attendance history logged yet.
                </div>
              ) : (
                <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-3 font-semibold">Date</th>
                        <th className="px-4 py-3 font-semibold">Check-In</th>
                        <th className="px-4 py-3 font-semibold">Check-Out</th>
                        <th className="px-4 py-3 font-semibold text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
                      {historyList.map((h, i) => (
                        <tr key={i} className="hover:bg-slate-800/30">
                          <td className="px-4 py-3 text-slate-200 font-semibold">{h.date}</td>
                          <td className="px-4 py-3 text-emerald-400">
                            {h.check_in_time ? (
                              <span className="flex items-center gap-1">
                                <LogIn className="w-3 h-3" /> {h.check_in_time}
                              </span>
                            ) : (
                              "--"
                            )}
                          </td>
                          <td className="px-4 py-3 text-amber-400">
                            {h.check_out_time ? (
                              <span className="flex items-center gap-1">
                                <LogOut className="w-3 h-3" /> {h.check_out_time}
                              </span>
                            ) : (
                              "--"
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                h.status === "CHECKED_OUT"
                                  ? "bg-amber-950/80 text-amber-300 border border-amber-500/30"
                                  : "bg-emerald-950/80 text-emerald-300 border border-emerald-500/30"
                              }`}
                            >
                              {h.status || "PRESENT"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

// Compatibility export
export const StudentDetailModal = EmployeeDetailModal;
