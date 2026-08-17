"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Search,
  Calendar as CalendarIcon,
  Download,
  Filter,
  CheckCircle2,
  AlertCircle,
  LogIn,
  LogOut,
  ChevronLeft,
  ChevronRight,
  User,
  Fingerprint,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { ManualCheckInModal } from "@/components/ManualCheckInModal";
import { AddEmployeeModal } from "@/components/AddEmployeeModal";
import { api, AttendanceRecord } from "@/lib/api";

export default function AttendancePage() {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters & Pagination
  const [search, setSearch] = useState<string>("");
  const [dateFilter, setDateFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [page, setPage] = useState<number>(1);
  const pageSize = 15;

  // Modals
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [addEmployeeModalOpen, setAddEmployeeModalOpen] = useState(false);

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAttendanceRecords({
        search: search || undefined,
        date: dateFilter || undefined,
        status: statusFilter || undefined,
        page,
        page_size: pageSize,
      });
      setRecords(data.records);
      setTotalCount(data.total_count);
    } catch (err) {
      console.error("Failed to load attendance records", err);
    } finally {
      setLoading(false);
    }
  }, [search, dateFilter, statusFilter, page]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  // Export to CSV
  const handleExportCSV = () => {
    if (records.length === 0) return;
    const headers = ["ID", "Employee ID", "Employee Name", "Date", "Check-In Time", "Check-Out Time", "Status"];
    const rows = records.map((r) => [
      r.id,
      r.employee_id || r.student_id,
      `"${r.employee_name || r.student_name}"`,
      r.date,
      r.check_in_time || "",
      r.check_out_time || "",
      r.status || "",
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `employee_attendance_${dateFilter || "all"}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const totalPages = Math.ceil(totalCount / pageSize) || 1;

  return (
    <div className="flex-1 flex flex-col">
      <Navbar
        title="Employee Attendance Records"
        subtitle="Historical and daily check-in / check-out audit records"
        onRefresh={fetchRecords}
        onOpenManualModal={() => setManualModalOpen(true)}
        onOpenAddEmployeeModal={() => setAddEmployeeModalOpen(true)}
      />

      <main className="p-8 space-y-6 max-w-7xl mx-auto w-full">
        {/* Filter Bar */}
        <div className="glass-panel rounded-2xl p-5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
            {/* Search Input */}
            <div className="relative flex-1 min-w-[200px] max-w-md">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by employee name or ID..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900/80 border border-slate-700 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 transition"
              />
            </div>

            {/* Date Picker Filter */}
            <div className="relative">
              <input
                type="date"
                value={dateFilter}
                onChange={(e) => {
                  setDateFilter(e.target.value);
                  setPage(1);
                }}
                className="pl-3.5 pr-3 py-2 rounded-xl bg-slate-900/80 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 transition font-mono"
              />
            </div>

            {/* Status Dropdown */}
            <div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="px-3.5 py-2 rounded-xl bg-slate-900/80 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 transition"
              >
                <option value="">All Statuses</option>
                <option value="CHECKED_IN">In Office (Checked In)</option>
                <option value="CHECKED_OUT">Departed (Checked Out)</option>
              </select>
            </div>

            {(search || dateFilter || statusFilter) && (
              <button
                onClick={() => {
                  setSearch("");
                  setDateFilter("");
                  setStatusFilter("");
                  setPage(1);
                }}
                className="text-xs text-rose-400 hover:text-rose-300 font-semibold px-2 py-1"
              >
                Clear Filters
              </button>
            )}
          </div>

          {/* Export Actions */}
          <button
            onClick={handleExportCSV}
            disabled={records.length === 0}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900/80 border border-slate-700 hover:border-slate-600 text-slate-200 text-xs font-semibold shadow-sm transition disabled:opacity-40"
          >
            <Download className="w-4 h-4 text-cyan-400" />
            <span>Export CSV</span>
          </button>
        </div>

        {/* Table Container */}
        <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/70 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-6 py-4">Employee</th>
                  <th className="px-6 py-4">Badge / ID</th>
                  <th className="px-6 py-4">Date</th>
                  <th className="px-6 py-4">Check-In Time</th>
                  <th className="px-6 py-4">Check-Out Time</th>
                  <th className="px-6 py-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="text-center py-20 text-slate-500">
                      Loading attendance records...
                    </td>
                  </tr>
                ) : records.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-20 text-slate-500">
                      No attendance records found matching the query.
                    </td>
                  </tr>
                ) : (
                  records.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-900/40 transition-colors">
                      <td className="px-6 py-4 font-sans font-semibold text-slate-100 flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-[11px] font-bold text-cyan-400">
                          {(row.employee_name || row.student_name).charAt(0).toUpperCase()}
                        </div>
                        <span>{row.employee_name || row.student_name}</span>
                      </td>
                      <td className="px-6 py-4 text-slate-400">
                        #{row.employee_id || row.student_id}
                      </td>
                      <td className="px-6 py-4 text-slate-300">{row.date}</td>
                      <td className="px-6 py-4 text-emerald-400">
                        {row.check_in_time ? (
                          <span className="flex items-center gap-1.5 font-semibold">
                            <LogIn className="w-3.5 h-3.5" />
                            {row.check_in_time}
                          </span>
                        ) : (
                          <span className="text-slate-600">--</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-amber-400">
                        {row.check_out_time ? (
                          <span className="flex items-center gap-1.5 font-semibold">
                            <LogOut className="w-3.5 h-3.5" />
                            {row.check_out_time}
                          </span>
                        ) : (
                          <span className="text-slate-600">--</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span
                          className={`inline-block text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                            row.status === "CHECKED_OUT"
                              ? "bg-amber-950/80 text-amber-300 border border-amber-500/30"
                              : "bg-emerald-950/80 text-emerald-300 border border-emerald-500/30"
                          }`}
                        >
                          {row.status === "CHECKED_OUT" ? "CHECKED OUT" : "IN OFFICE"}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="p-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <div>
              Showing <span className="font-semibold text-slate-200">{records.length}</span> of{" "}
              <span className="font-semibold text-slate-200">{totalCount}</span> total logs
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:border-slate-700 disabled:opacity-40 transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-mono text-xs px-2">
                Page {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:border-slate-700 disabled:opacity-40 transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Modals */}
      <ManualCheckInModal
        isOpen={manualModalOpen}
        onClose={() => setManualModalOpen(false)}
        onSuccess={fetchRecords}
      />

      <AddEmployeeModal
        isOpen={addEmployeeModalOpen}
        onClose={() => setAddEmployeeModalOpen(false)}
        onSuccess={fetchRecords}
      />
    </div>
  );
}
