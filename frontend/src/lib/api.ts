/**
 * API Client for FastAPI Attendance Backend
 */

// If NEXT_PUBLIC_API_URL is set, use it; otherwise use empty string in browser (to leverage Next.js proxy) or localhost in SSR
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" ? "" : "http://127.0.0.1:8000");

export interface SummaryMetrics {
  total_students: number;
  total_employees?: number;
  present_today: number;
  checked_in_now: number;
  checked_out_today: number;
  absent_today: number;
  attendance_rate: number;
  today_logs_count: number;
  today_date: string;
}

export interface DayTrend {
  date: string;
  day_name: string;
  present: number;
  checked_out: number;
  total_students: number;
  rate: number;
}

export interface HourlyCount {
  hour: string;
  check_ins: number;
  check_outs: number;
}

export interface AttendanceRecord {
  id: number;
  student_id: number;
  employee_id?: number;
  student_name: string;
  employee_name?: string;
  date: string;
  check_in_time: string | null;
  check_out_time: string | null;
  status: string | null;
}

export interface AttendanceListResponse {
  records: AttendanceRecord[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface Employee {
  id: number;
  name: string;
  total_attendances: number;
  last_attended_date: string | null;
  attendance_rate: number;
}

export type Student = Employee;

export interface EmployeeDetail extends Employee {
  history: Array<{
    date: string;
    check_in_time: string | null;
    check_out_time: string | null;
    status: string | null;
  }>;
}

export type StudentDetail = EmployeeDetail;

export interface ActivityLog {
  id: number;
  student_id: number;
  employee_id?: number;
  student_name: string;
  employee_name?: string;
  action: string;
  date: string;
  time: string;
  timestamp: string;
}

async function fetchJson<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let errorDetail = `API Error ${res.status}: ${res.statusText}`;
    try {
      const err = await res.json();
      if (err.detail) errorDetail = err.detail;
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // Health
  getHealth: () => fetchJson<{ status: string; service: string }>("/api/health"),

  // Analytics
  getSummary: () => fetchJson<SummaryMetrics>("/api/analytics/summary"),
  getWeeklyTrend: () => fetchJson<DayTrend[]>("/api/analytics/weekly"),
  getHourlyDistribution: () =>
    fetchJson<HourlyCount[]>("/api/analytics/hourly"),

  // Attendance
  getAttendanceRecords: (params?: {
    date?: string;
    student_id?: number;
    employee_id?: number;
    status?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.date) q.append("date", params.date);
    if (params?.student_id || params?.employee_id)
      q.append("student_id", (params.employee_id || params.student_id)!.toString());
    if (params?.status) q.append("status", params.status);
    if (params?.search) q.append("search", params.search);
    if (params?.page) q.append("page", params.page.toString());
    if (params?.page_size) q.append("page_size", params.page_size.toString());
    return fetchJson<AttendanceListResponse>(
      `/api/attendance${q.toString() ? `?${q.toString()}` : ""}`
    );
  },

  recordManualAttendance: (data: {
    student_id: number;
    action: "CHECK_IN" | "CHECK_OUT";
    date?: string;
    time?: string;
  }) =>
    fetchJson<{ success: boolean; student_name: string; action: string }>(
      "/api/attendance/manual",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  // Employees & Faculty
  getEmployees: (search?: string) =>
    fetchJson<Employee[]>(
      `/api/employees${search ? `?search=${encodeURIComponent(search)}` : ""}`
    ),
  getStudents: (search?: string) =>
    fetchJson<Employee[]>(
      `/api/employees${search ? `?search=${encodeURIComponent(search)}` : ""}`
    ),

  getEmployeeDetail: (id: number) =>
    fetchJson<EmployeeDetail>(`/api/employees/${id}`),
  getStudentDetail: (id: number) =>
    fetchJson<EmployeeDetail>(`/api/employees/${id}`),

  addEmployee: (data: { id?: number; name: string }) =>
    fetchJson<{ id: number; name: string }>("/api/employees", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  addStudent: (data: { id?: number; name: string }) =>
    fetchJson<{ id: number; name: string }>("/api/employees", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteEmployee: (id: number) =>
    fetchJson<{ success: boolean; message: string }>(`/api/employees/${id}`, {
      method: "DELETE",
    }),
  deleteStudent: (id: number) =>
    fetchJson<{ success: boolean; message: string }>(`/api/employees/${id}`, {
      method: "DELETE",
    }),

  // Logs
  getLogs: (params?: { limit?: number; student_id?: number }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.append("limit", params.limit.toString());
    if (params?.student_id) q.append("student_id", params.student_id.toString());
    return fetchJson<ActivityLog[]>(
      `/api/logs${q.toString() ? `?${q.toString()}` : ""}`
    );
  },
};
