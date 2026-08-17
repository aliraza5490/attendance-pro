"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Users,
  UserCheck,
  UserX,
  Clock,
  TrendingUp,
  Activity,
  ArrowUpRight,
  Sparkles,
  Building2,
  Calendar,
  LogIn,
  LogOut,
} from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Navbar } from "@/components/Navbar";
import { MetricCard } from "@/components/MetricCard";
import { ManualCheckInModal } from "@/components/ManualCheckInModal";
import { AddEmployeeModal } from "@/components/AddEmployeeModal";
import {
  api,
  SummaryMetrics,
  DayTrend,
  HourlyCount,
  ActivityLog,
} from "@/lib/api";

export default function OverviewPage() {
  const [summary, setSummary] = useState<SummaryMetrics | null>(null);
  const [weeklyTrends, setWeeklyTrends] = useState<DayTrend[]>([]);
  const [hourlyData, setHourlyData] = useState<HourlyCount[]>([]);
  const [recentLogs, setRecentLogs] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Modals
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [addEmployeeModalOpen, setAddEmployeeModalOpen] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [sum, weekly, hourly, logs] = await Promise.all([
        api.getSummary(),
        api.getWeeklyTrend(),
        api.getHourlyDistribution(),
        api.getLogs({ limit: 6 }),
      ]);
      setSummary(sum);
      setWeeklyTrends(weekly);
      setHourlyData(hourly);
      setRecentLogs(logs);
    } catch (err) {
      console.error("Failed to load dashboard metrics", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000); // 8s periodic poll
    return () => clearInterval(interval);
  }, [fetchData]);

  const totalEmployees = summary?.total_employees ?? summary?.total_students ?? 0;

  return (
    <div className="flex-1 flex flex-col">
      <Navbar
        title="Workplace Overview"
        subtitle="Real-time employee attendance analytics and recognition stream"
        onRefresh={fetchData}
        onOpenManualModal={() => setManualModalOpen(true)}
        onOpenAddEmployeeModal={() => setAddEmployeeModalOpen(true)}
      />

      <main className="p-8 space-y-8 max-w-7xl mx-auto w-full">
        {/* KPI Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total Registered Staff"
            value={summary ? totalEmployees : "--"}
            subtext="Registered in biometric database"
            icon={Users}
            accentColor="cyan"
            loading={loading}
          />
          <MetricCard
            title="Present Today"
            value={summary ? summary.present_today : "--"}
            subtext={
              summary
                ? `${summary.attendance_rate}% of workforce active`
                : "Active today"
            }
            icon={UserCheck}
            accentColor="emerald"
            badge="ON SITE"
            badgeVariant="emerald"
            loading={loading}
          />
          <MetricCard
            title="In Office Now"
            value={summary ? summary.checked_in_now : "--"}
            subtext="Currently checked in"
            icon={Building2}
            accentColor="indigo"
            badge="ACTIVE"
            badgeVariant="cyan"
            loading={loading}
          />
          <MetricCard
            title="Checked Out Today"
            value={summary ? summary.checked_out_today : "--"}
            subtext={`${summary?.absent_today ?? 0} not checked in`}
            icon={LogOut}
            accentColor="amber"
            badge="DEPARTED"
            badgeVariant="amber"
            loading={loading}
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Weekly Attendance Trend (Area Chart) */}
          <div className="lg:col-span-2 glass-panel rounded-2xl p-6 relative">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-cyan-400" />
                  Weekly Staff Attendance Trend
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Daily presence rate over the past 7 days
                </p>
              </div>
              <span className="text-xs font-mono text-cyan-300 bg-cyan-950/80 px-2.5 py-1 rounded-lg border border-cyan-500/30">
                Avg: {summary?.attendance_rate ?? 0}%
              </span>
            </div>

            <div className="h-72 w-full">
              {loading ? (
                <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                  Loading trend telemetry...
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={weeklyTrends}
                    margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                  >
                    <defs>
                      <linearGradient id="cyanGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                      dataKey="day_name"
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "0.75rem",
                        color: "#f8fafc",
                        fontSize: "12px",
                      }}
                      itemStyle={{ color: "#22d3ee" }}
                    />
                    <Area
                      type="monotone"
                      dataKey="present"
                      name="Staff Present"
                      stroke="#06b6d4"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#cyanGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Hourly Traffic Distribution (Bar Chart) */}
          <div className="glass-panel rounded-2xl p-6 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-indigo-400" />
                  Peak Arrival Hours
                </h3>
                <span className="text-[11px] font-mono text-slate-400">Today</span>
              </div>
              <p className="text-xs text-slate-400 mb-6">
                Hourly breakdown of check-ins vs check-outs
              </p>
            </div>

            <div className="h-64 w-full">
              {loading ? (
                <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                  Loading hourly stats...
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={hourlyData}
                    margin={{ top: 0, right: 0, left: -25, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                      dataKey="hour"
                      stroke="#64748b"
                      fontSize={10}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={10}
                      tickLine={false}
                      axisLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "0.75rem",
                        color: "#f8fafc",
                        fontSize: "11px",
                      }}
                    />
                    <Bar
                      dataKey="check_ins"
                      name="Check-Ins"
                      fill="#10b981"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="check_outs"
                      name="Check-Outs"
                      fill="#f59e0b"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="flex items-center justify-center gap-6 pt-4 border-t border-slate-800/80 text-xs">
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
                <span>Check-Ins</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-sm bg-amber-500" />
                <span>Check-Outs</span>
              </div>
            </div>
          </div>
        </div>

        {/* Live Activity Feed */}
        <div className="glass-panel rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                Live Staff Biometric Stream
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Real-time recognition and gesture events logged by vision nodes
              </p>
            </div>
            <a
              href="/live"
              className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition"
            >
              Open Live Stream <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>

          {recentLogs.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-xs">
              No staff attendance activity recorded today yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentLogs.map((log) => {
                const name = log.employee_name || log.student_name;
                const empId = log.employee_id || log.student_id;
                return (
                  <div
                    key={log.id}
                    className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 flex items-center justify-between hover:bg-slate-900/80 transition"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`p-2 rounded-xl ${
                          log.action === "CHECK_IN"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                        }`}
                      >
                        {log.action === "CHECK_IN" ? (
                          <LogIn className="w-4 h-4" />
                        ) : (
                          <LogOut className="w-4 h-4" />
                        )}
                      </div>
                      <div>
                        <div className="text-xs font-bold text-slate-200">
                          {name}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          Badge #{empId} •{" "}
                          <span
                            className={
                              log.action === "CHECK_IN"
                                ? "text-emerald-400 font-semibold"
                                : "text-amber-400 font-semibold"
                            }
                          >
                            {log.action === "CHECK_IN" ? "Checked In" : "Checked Out"}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="text-right font-mono text-[11px] text-slate-400">
                      {log.time}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {/* Modals */}
      <ManualCheckInModal
        isOpen={manualModalOpen}
        onClose={() => setManualModalOpen(false)}
        onSuccess={fetchData}
      />

      <AddEmployeeModal
        isOpen={addEmployeeModalOpen}
        onClose={() => setAddEmployeeModalOpen(false)}
        onSuccess={fetchData}
      />
    </div>
  );
}
