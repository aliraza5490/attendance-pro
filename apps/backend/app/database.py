"""Database connection and query helper functions."""

from datetime import date, datetime, timedelta
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

# Resolve path to attendance.db
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(
    os.environ.get(
        "DATABASE_PATH",
        (BASE_DIR.parent.parent.parent / "attendance.db")
        if (BASE_DIR.parent.parent.parent / "attendance.db").exists()
        else (BASE_DIR.parent.parent / "attendance.db")
        if (BASE_DIR.parent.parent / "attendance.db").exists()
        else BASE_DIR / "attendance.db",
    )
)


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with dict-like row factory."""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Ensure database schema tables and indexes exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT,
                check_in_time TEXT,
                check_out_time TEXT,
                status TEXT,
                UNIQUE(student_id, date)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        conn.commit()


# ==============================================================================
# Analytics & KPI Queries
# ==============================================================================

def get_summary_metrics() -> Dict[str, Any]:
    """Calculate key attendance metrics for today."""
    today_str = date.today().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()

        # Total registered students
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0] or 0

        # Today's attendance records
        cursor.execute(
            """
            SELECT
                COUNT(CASE WHEN check_in_time IS NOT NULL THEN 1 END) AS present_count,
                COUNT(CASE WHEN status = 'CHECKED_IN' THEN 1 END) AS checked_in_count,
                COUNT(CASE WHEN status = 'CHECKED_OUT' THEN 1 END) AS checked_out_count
            FROM attendance
            WHERE date = ?
            """,
            (today_str,),
        )
        att_row = cursor.fetchone()
        present_today = att_row["present_count"] or 0
        checked_in_now = att_row["checked_in_count"] or 0
        checked_out_today = att_row["checked_out_count"] or 0

        absent_today = max(0, total_students - present_today)
        rate = round((present_today / total_students * 100), 1) if total_students > 0 else 0.0

        # Total logs today
        cursor.execute(
            "SELECT COUNT(*) FROM attendance_logs WHERE date = ?",
            (today_str,),
        )
        today_logs = cursor.fetchone()[0] or 0

        return {
            "total_students": total_students,
            "present_today": present_today,
            "checked_in_now": checked_in_now,
            "checked_out_today": checked_out_today,
            "absent_today": absent_today,
            "attendance_rate": rate,
            "today_logs_count": today_logs,
            "today_date": today_str,
        }


def get_weekly_trend(days: int = 7) -> List[Dict[str, Any]]:
    """Get attendance counts for the past N days."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0] or 0

        cursor.execute(
            """
            SELECT
                date,
                COUNT(CASE WHEN check_in_time IS NOT NULL THEN 1 END) AS present_count,
                COUNT(CASE WHEN status = 'CHECKED_OUT' THEN 1 END) AS checked_out_count
            FROM attendance
            WHERE date >= ? AND date <= ?
            GROUP BY date
            """,
            (start_date.isoformat(), end_date.isoformat()),
        )
        date_map = {row["date"]: row for row in cursor.fetchall()}

    results = []
    current = start_date
    while current <= end_date:
        d_str = current.isoformat()
        day_name = current.strftime("%a")
        row = date_map.get(d_str)
        present = row["present_count"] if row else 0
        checked_out = row["checked_out_count"] if row else 0
        rate = round((present / total_students * 100), 1) if total_students > 0 else 0.0

        results.append({
            "date": d_str,
            "day_name": day_name,
            "present": present,
            "checked_out": checked_out,
            "total_students": total_students,
            "rate": rate,
        })
        current += timedelta(days=1)

    return results


def get_hourly_distribution(target_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get count of check-ins and check-outs by hour for a specific date."""
    query_date = target_date or date.today().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                strftime('%H:00', time) as hour_slot,
                action,
                COUNT(*) as count
            FROM attendance_logs
            WHERE date = ?
            GROUP BY hour_slot, action
            ORDER BY hour_slot ASC
            """,
            (query_date,),
        )
        rows = cursor.fetchall()

    slots: Dict[str, Dict[str, int]] = {}
    for h in range(8, 19):
        hour_str = f"{h:02d}:00"
        slots[hour_str] = {"check_ins": 0, "check_outs": 0}

    for row in rows:
        h = row["hour_slot"]
        if h not in slots:
            slots[h] = {"check_ins": 0, "check_outs": 0}
        if row["action"] == "CHECK_IN":
            slots[h]["check_ins"] += row["count"]
        elif row["action"] == "CHECK_OUT":
            slots[h]["check_outs"] += row["count"]

    return [
        {"hour": h, "check_ins": data["check_ins"], "check_outs": data["check_outs"]}
        for h, data in sorted(slots.items())
    ]


# ==============================================================================
# Attendance Record Queries
# ==============================================================================

def get_attendance_records(
    date_filter: Optional[str] = None,
    student_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Dict[str, Any]], int]:
    """Retrieve filtered attendance records with student information."""
    with get_connection() as conn:
        cursor = conn.cursor()

        conditions = ["1=1"]
        params: List[Any] = []

        if date_filter:
            conditions.append("a.date = ?")
            params.append(date_filter)

        if student_id is not None:
            conditions.append("a.student_id = ?")
            params.append(student_id)

        if status_filter:
            conditions.append("a.status = ?")
            params.append(status_filter)

        if search:
            conditions.append("(s.name LIKE ? OR CAST(s.id AS TEXT) LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param])

        where_clause = " AND ".join(conditions)

        # Count total
        count_sql = f"""
            SELECT COUNT(*)
            FROM attendance a
            LEFT JOIN students s ON a.student_id = s.id
            WHERE {where_clause}
        """
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

        # Fetch records
        sql = f"""
            SELECT
                a.id,
                a.student_id,
                COALESCE(s.name, 'Unknown Student') as student_name,
                a.date,
                COALESCE(a.check_in_time, a.time) as check_in_time,
                a.check_out_time,
                COALESCE(a.status, 'CHECKED_IN') as status
            FROM attendance a
            LEFT JOIN students s ON a.student_id = s.id
            WHERE {where_clause}
            ORDER BY a.date DESC, COALESCE(a.check_in_time, a.time) DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(sql, params + [limit, offset])
        records = [dict(row) for row in cursor.fetchall()]

        return records, total_count


def record_manual_attendance(
    student_id: int,
    action: str,
    action_date: Optional[str] = None,
    action_time: Optional[str] = None,
) -> Dict[str, Any]:
    """Record manual check-in or check-out for a student."""
    now = datetime.now()
    cur_date = action_date or now.strftime("%Y-%m-%d")
    cur_time = action_time or now.strftime("%H:%M:%S")
    timestamp = now.isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if student exists
        cursor.execute("SELECT name FROM students WHERE id = ?", (student_id,))
        s_row = cursor.fetchone()
        if not s_row:
            raise ValueError(f"Student with ID {student_id} not found.")

        student_name = s_row["name"]

        # Insert audit log
        cursor.execute(
            """
            INSERT INTO attendance_logs (student_id, action, date, time, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_id, action, cur_date, cur_time, timestamp),
        )

        # Update attendance table
        cursor.execute(
            "SELECT id, check_in_time, check_out_time, status FROM attendance WHERE student_id = ? AND date = ?",
            (student_id, cur_date),
        )
        existing = cursor.fetchone()

        if action == "CHECK_IN":
            if existing:
                cursor.execute(
                    """
                    UPDATE attendance
                    SET check_in_time = ?, time = ?, status = 'CHECKED_IN'
                    WHERE id = ?
                    """,
                    (cur_time, cur_time, existing["id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO attendance (student_id, date, time, check_in_time, check_out_time, status)
                    VALUES (?, ?, ?, ?, NULL, 'CHECKED_IN')
                    """,
                    (student_id, cur_date, cur_time, cur_time),
                )
        elif action == "CHECK_OUT":
            if existing:
                cursor.execute(
                    """
                    UPDATE attendance
                    SET check_out_time = ?, status = 'CHECKED_OUT'
                    WHERE id = ?
                    """,
                    (cur_time, existing["id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO attendance (student_id, date, time, check_in_time, check_out_time, status)
                    VALUES (?, ?, ?, NULL, ?, 'CHECKED_OUT')
                    """,
                    (student_id, cur_date, cur_time, cur_time),
                )

        conn.commit()

        return {
            "success": True,
            "student_id": student_id,
            "student_name": student_name,
            "action": action,
            "date": cur_date,
            "time": cur_time,
        }


# ==============================================================================
# Students Queries
# ==============================================================================

def get_students(search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all students with their attendance statistics."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Count total active unique attendance dates to calculate individual rate
        cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
        total_session_days = cursor.fetchone()[0] or 1

        sql = """
            SELECT
                s.id,
                s.name,
                COUNT(a.id) as total_attendances,
                MAX(a.date) as last_attended_date
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
        """
        params: List[Any] = []
        if search:
            sql += " WHERE s.name LIKE ? OR CAST(s.id AS TEXT) LIKE ?"
            params.extend([f"%{search}%", f"%{search}%"])

        sql += " GROUP BY s.id, s.name ORDER BY s.id ASC"
        cursor.execute(sql, params)

        results = []
        for row in cursor.fetchall():
            tot = row["total_attendances"] or 0
            rate = round((tot / total_session_days * 100), 1) if total_session_days > 0 else 0.0
            results.append({
                "id": row["id"],
                "name": row["name"],
                "total_attendances": tot,
                "last_attended_date": row["last_attended_date"],
                "attendance_rate": min(100.0, rate),
            })
        return results


def get_student_by_id(student_id: int) -> Optional[Dict[str, Any]]:
    """Fetch student detail along with their attendance metrics, history, and logs."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM students WHERE id = ?", (student_id,))
        s_row = cursor.fetchone()
        if not s_row:
            return None

        # Calculate total active days and student attendances
        cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
        total_session_days = cursor.fetchone()[0] or 1

        cursor.execute(
            """
            SELECT id, date, check_in_time, check_out_time, status
            FROM attendance
            WHERE student_id = ?
            ORDER BY date DESC
            LIMIT 50
            """,
            (student_id,),
        )
        records = [dict(r) for r in cursor.fetchall()]

        total_attendances = len(records)
        last_date = records[0]["date"] if records else None
        rate = round((total_attendances / total_session_days * 100), 1) if total_session_days > 0 else 0.0

        cursor.execute(
            """
            SELECT id, action, date, time, timestamp
            FROM attendance_logs
            WHERE student_id = ?
            ORDER BY timestamp DESC
            LIMIT 20
            """,
            (student_id,),
        )
        logs = [dict(r) for r in cursor.fetchall()]

        return {
            "id": s_row["id"],
            "name": s_row["name"],
            "total_attendances": total_attendances,
            "last_attended_date": last_date,
            "attendance_rate": min(100.0, rate),
            "history": records,
            "records": records,
            "logs": logs,
        }


def add_student(name: str, student_id: Optional[int] = None) -> Dict[str, Any]:
    """Add a new student to the database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if student_id is not None:
            cursor.execute("INSERT INTO students (id, name) VALUES (?, ?)", (student_id, name))
            new_id = student_id
        else:
            cursor.execute("INSERT INTO students (name) VALUES (?)", (name,))
            new_id = cursor.lastrowid
        conn.commit()
        return {"id": new_id, "name": name}


def remove_student(student_id: int) -> bool:
    """Delete a student and their associated attendance logs."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM attendance_logs WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
        return cursor.rowcount > 0


# ==============================================================================
# Activity Logs Queries
# ==============================================================================

def get_activity_logs(
    limit: int = 50,
    date_filter: Optional[str] = None,
    action_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve audit activity logs joined with student name."""
    with get_connection() as conn:
        cursor = conn.cursor()
        conditions = ["1=1"]
        params: List[Any] = []

        if date_filter:
            conditions.append("l.date = ?")
            params.append(date_filter)

        if action_filter:
            conditions.append("l.action = ?")
            params.append(action_filter)

        where_clause = " AND ".join(conditions)

        sql = f"""
            SELECT
                l.id,
                l.student_id,
                COALESCE(s.name, 'Unknown Student') as student_name,
                l.action,
                l.date,
                l.time,
                l.timestamp
            FROM attendance_logs l
            LEFT JOIN students s ON l.student_id = s.id
            WHERE {where_clause}
            ORDER BY l.id DESC
            LIMIT ?
        """
        cursor.execute(sql, params + [limit])
        return [dict(row) for row in cursor.fetchall()]
