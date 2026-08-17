"use client";

import React, { useState, useEffect } from "react";
import { X, LogIn, LogOut, CheckCircle2, AlertCircle } from "lucide-react";
import { api, Employee } from "@/lib/api";

interface ManualCheckInModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function ManualCheckInModal({
  isOpen,
  onClose,
  onSuccess,
}: ManualCheckInModalProps) {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string>("");
  const [action, setAction] = useState<"CHECK_IN" | "CHECK_OUT">("CHECK_IN");
  const [customTime, setCustomTime] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setError(null);
      setSuccessMsg(null);
      api
        .getEmployees()
        .then((data) => {
          setEmployees(data);
          if (data.length > 0 && !selectedEmployeeId) {
            setSelectedEmployeeId(data[0].id.toString());
          }
        })
        .catch(() => {
          setError("Failed to load employee list");
        });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEmployeeId) {
      setError("Please select an employee");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.recordManualAttendance({
        student_id: parseInt(selectedEmployeeId, 10),
        action,
        time: customTime || undefined,
      });
      setSuccessMsg(
        `Successfully recorded ${action.replace("_", " ")} for ${res.student_name}!`
      );
      if (onSuccess) onSuccess();
      setTimeout(() => {
        onClose();
      }, 1200);
    } catch (err: any) {
      setError(err.message || "Failed to record manual attendance");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-panel w-full max-w-md rounded-2xl p-6 shadow-2xl border border-slate-700/80 relative">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-slate-100">Manual Attendance Entry</h2>
            <p className="text-xs text-slate-400">Override check-in/out for an employee</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Feedback Alerts */}
        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-2 text-rose-400 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {successMsg && (
          <div className="mt-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-2 text-emerald-400 text-xs">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Employee Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Select Employee / Staff Member
            </label>
            <select
              value={selectedEmployeeId}
              onChange={(e) => setSelectedEmployeeId(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 text-sm focus:outline-none focus:border-cyan-500 transition"
            >
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  ID #{emp.id} — {emp.name}
                </option>
              ))}
            </select>
          </div>

          {/* Action Radio Buttons */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Select Action
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setAction("CHECK_IN")}
                className={`flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-semibold border transition ${
                  action === "CHECK_IN"
                    ? "bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-lg shadow-emerald-500/10"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <LogIn className="w-4 h-4" />
                <span>Check-In</span>
              </button>

              <button
                type="button"
                onClick={() => setAction("CHECK_OUT")}
                className={`flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-semibold border transition ${
                  action === "CHECK_OUT"
                    ? "bg-amber-500/20 border-amber-500 text-amber-300 shadow-lg shadow-amber-500/10"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <LogOut className="w-4 h-4" />
                <span>Check-Out</span>
              </button>
            </div>
          </div>

          {/* Custom Time (Optional) */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Override Time (Optional - defaults to now)
            </label>
            <input
              type="time"
              step="1"
              value={customTime}
              onChange={(e) => setCustomTime(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 text-sm focus:outline-none focus:border-cyan-500 transition font-mono"
            />
          </div>

          {/* Submit */}
          <div className="pt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-cyan-600/20 transition disabled:opacity-50"
            >
              {loading ? "Recording..." : "Confirm Attendance"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
