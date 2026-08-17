"use client";

import React, { useState } from "react";
import { X, UserPlus, AlertCircle, CheckCircle2, Building, Hash } from "lucide-react";
import { api } from "@/lib/api";

interface AddEmployeeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function AddEmployeeModal({
  isOpen,
  onClose,
  onSuccess,
}: AddEmployeeModalProps) {
  const [employeeId, setEmployeeId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter the employee's full name");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const parsedId = employeeId ? parseInt(employeeId, 10) : undefined;
      const res = await api.addEmployee({
        id: parsedId,
        name: name.trim(),
      });
      setSuccessMsg(`Employee #${res.id} (${res.name}) successfully registered!`);
      if (onSuccess) onSuccess();
      setTimeout(() => {
        setName("");
        setEmployeeId("");
        setSuccessMsg(null);
        onClose();
      }, 1300);
    } catch (err: any) {
      setError(err.message || "Failed to register employee");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-panel w-full max-w-md rounded-2xl p-6 shadow-2xl border border-slate-700/80 relative">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-cyan-400" />
              Register Employee / Faculty
            </h2>
            <p className="text-xs text-slate-400">
              Add a new staff member to the attendance registry
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

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

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
              <Hash className="w-3.5 h-3.5 text-cyan-400" /> Employee / Badge ID (Optional)
            </label>
            <input
              type="number"
              min="1"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              placeholder="e.g. 101 (auto-assigned if left blank)"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 text-sm focus:outline-none focus:border-cyan-500 transition font-mono placeholder:text-slate-600"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
              <Building className="w-3.5 h-3.5 text-indigo-400" /> Employee Full Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Sarah Connor, Dr. Alex Mitchell"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-200 text-sm focus:outline-none focus:border-cyan-500 transition placeholder:text-slate-600"
            />
          </div>

          <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/20 text-[11px] text-cyan-300">
            💡 <strong>Next Step:</strong> After registering, run the capture utility to enroll face samples:
            <div className="font-mono text-[10px] mt-1 text-slate-400">
              uv run --package attendance-tracker capture
            </div>
          </div>

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
              {loading ? "Registering..." : "Save Employee"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Alias for backwards compatibility
export const AddStudentModal = AddEmployeeModal;
