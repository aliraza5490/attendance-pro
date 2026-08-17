"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Search,
  UserPlus,
  Trash2,
  Eye,
  Calendar,
  TrendingUp,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Building,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ManualCheckInModal } from "@/components/ManualCheckInModal";
import { AddEmployeeModal } from "@/components/AddEmployeeModal";
import { EmployeeDetailModal } from "@/components/EmployeeDetailModal";
import { api, Employee } from "@/lib/api";

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [search, setSearch] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  // Modals
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [addEmployeeModalOpen, setAddEmployeeModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);

  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getEmployees(search || undefined);
      setEmployees(data);
    } catch (err) {
      console.error("Failed to load employees", err);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  const handleDelete = async (id: number, name: string) => {
    if (
      !window.confirm(
        `Are you sure you want to remove employee #${id} (${name}) and their attendance history?`
      )
    ) {
      return;
    }
    try {
      await api.deleteEmployee(id);
      fetchEmployees();
    } catch (err) {
      alert("Failed to delete employee: " + (err as Error).message);
    }
  };

  const handleOpenDetail = (id: number) => {
    setSelectedEmployeeId(id);
    setDetailModalOpen(true);
  };

  return (
    <div className="flex-1 flex flex-col">
      <Navbar
        title="Employee & Faculty Directory"
        subtitle="Manage registered faculty, staff, and office personnel"
        onRefresh={fetchEmployees}
        onOpenManualModal={() => setManualModalOpen(true)}
        onOpenAddEmployeeModal={() => setAddEmployeeModalOpen(true)}
      />

      <main className="p-8 space-y-6 max-w-7xl mx-auto w-full">
        {/* Action & Search Bar */}
        <div className="glass-panel rounded-2xl p-5 flex flex-wrap items-center justify-between gap-4">
          <div className="relative flex-1 min-w-[260px] max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search faculty / staff by name or badge ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900/80 border border-slate-700 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 transition"
            />
          </div>

          <button
            onClick={() => setAddEmployeeModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-cyan-600/20 transition"
          >
            <UserPlus className="w-4 h-4" />
            <span>Add New Employee</span>
          </button>
        </div>

        {/* Employees Grid */}
        {loading ? (
          <div className="py-24 text-center text-slate-500 text-xs">
            Loading employee roster...
          </div>
        ) : employees.length === 0 ? (
          <div className="glass-panel rounded-2xl p-12 text-center text-slate-500 space-y-3">
            <Building className="w-10 h-10 mx-auto text-slate-600" />
            <p className="text-sm font-semibold text-slate-300">No staff members enrolled</p>
            <p className="text-xs text-slate-400">
              Click &quot;Add New Employee&quot; or run the face capture tool to register staff.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {employees.map((emp) => (
              <div
                key={emp.id}
                className="glass-panel rounded-2xl p-6 relative group hover:border-cyan-500/40 transition-all duration-200"
              >
                {/* Header Profile */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-600/30 to-indigo-600/30 border border-cyan-500/40 flex items-center justify-center font-bold text-base text-cyan-300 shadow-md">
                      {emp.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-bold text-sm text-slate-100 group-hover:text-cyan-300 transition">
                        {emp.name}
                      </h3>
                      <span className="text-[11px] font-mono text-slate-400">
                        Badge ID #{emp.id}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDelete(emp.id, emp.name)}
                    title="Remove Employee"
                    className="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {/* Progress Bar & Rate */}
                <div className="mt-5 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400 font-medium flex items-center gap-1">
                      <TrendingUp className="w-3.5 h-3.5 text-cyan-400" /> Attendance Rate
                    </span>
                    <span className="font-bold font-mono text-cyan-300">
                      {emp.attendance_rate}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, emp.attendance_rate)}%` }}
                    />
                  </div>
                </div>

                {/* Stats Footer */}
                <div className="mt-5 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
                  <div>
                    <div className="text-[10px] text-slate-400">Total Check-Ins</div>
                    <div className="font-mono font-bold text-slate-200">
                      {emp.total_attendances} days
                    </div>
                  </div>

                  <button
                    onClick={() => handleOpenDetail(emp.id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-semibold transition"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Profile</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Modals */}
      <ManualCheckInModal
        isOpen={manualModalOpen}
        onClose={() => setManualModalOpen(false)}
        onSuccess={fetchEmployees}
      />

      <AddEmployeeModal
        isOpen={addEmployeeModalOpen}
        onClose={() => setAddEmployeeModalOpen(false)}
        onSuccess={fetchEmployees}
      />

      <EmployeeDetailModal
        employeeId={selectedEmployeeId}
        isOpen={detailModalOpen}
        onClose={() => setDetailModalOpen(false)}
      />
    </div>
  );
}
