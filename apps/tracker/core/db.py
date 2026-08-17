"""Database operations, schema management, and attendance consistency logic."""

from datetime import datetime
from pathlib import Path
import sqlite3

from core.config import (
    ACTION_CHECK_IN,
    ACTION_CHECK_OUT,
    ACTION_COOLDOWN_SECONDS,
    DATABASE_PATH,
)


def parse_db_timestamp(
    timestamp_str: str | None,
    date_str: str | None = None,
    time_str: str | None = None,
) -> datetime | None:
    """Parse timestamp string or fallback to date + time combination."""
    if timestamp_str:
        try:
            return datetime.fromisoformat(timestamp_str)
        except Exception:
            try:
                return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
    if date_str and time_str:
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
    return None


def init_database(db_path: Path = DATABASE_PATH) -> None:
    """Ensure tables, columns, and indexes exist for attendance and audit logs."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Students table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
            """
        )

        # Attendance daily summary table
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

        # Migration: Ensure check_in_time, check_out_time, status exist
        cursor.execute("PRAGMA table_info(attendance)")
        columns = [row[1] for row in cursor.fetchall()]
        if "check_in_time" not in columns:
            cursor.execute("ALTER TABLE attendance ADD COLUMN check_in_time TEXT")
        if "check_out_time" not in columns:
            cursor.execute("ALTER TABLE attendance ADD COLUMN check_out_time TEXT")
        if "status" not in columns:
            cursor.execute("ALTER TABLE attendance ADD COLUMN status TEXT")

        # Detailed audit log for ALL check-in and check-out events
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
            """
        )

        # Indexes for optimized audit log lookup and consistency
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_student_id ON attendance_logs (student_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_logs_student_date ON attendance_logs (student_id, date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance (student_id, date)"
        )
        conn.commit()


def register_student(student_id: int, student_name: str, db_path: Path = DATABASE_PATH) -> None:
    """Insert or update a student record in the database."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO students (id, name)
            VALUES (?, ?)
            """,
            (student_id, student_name),
        )
        conn.commit()


def fetch_enrolled_students(db_path: Path = DATABASE_PATH) -> dict[int, str]:
    """Retrieve mapping of student_id -> student_name."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM students")
        return {row[0]: row[1] for row in cursor.fetchall()}


def get_student_today_summary(student_id: int, db_path: Path = DATABASE_PATH) -> dict:
    """Retrieve today's check-in/out counts, latest timestamps, and hourly cooldown status."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Fetch all log entries today for this student
        cursor.execute(
            """
            SELECT action, time, timestamp, date
            FROM attendance_logs
            WHERE student_id = ? AND date = ?
            ORDER BY id ASC
            """,
            (student_id, date_str),
        )
        rows = cursor.fetchall()

        ins = [r[1] for r in rows if r[0] == ACTION_CHECK_IN]
        outs = [r[1] for r in rows if r[0] == ACTION_CHECK_OUT]

        # Check most recent action overall to compute cooldown accurately
        cursor.execute(
            """
            SELECT action, timestamp, date, time
            FROM attendance_logs
            WHERE student_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (student_id,),
        )
        last_row = cursor.fetchone()

        cooldown_remaining = 0
        last_action_type = None
        last_action_time_str = None

        if last_row:
            last_action_type = last_row[0]
            last_action_time_str = last_row[3]
            dt = parse_db_timestamp(last_row[1], last_row[2], last_row[3])
            if dt:
                elapsed = (now - dt).total_seconds()
                if elapsed < ACTION_COOLDOWN_SECONDS:
                    cooldown_remaining = max(0, int(ACTION_COOLDOWN_SECONDS - elapsed))

        return {
            "check_in_count": len(ins),
            "check_out_count": len(outs),
            "last_check_in": ins[-1] if ins else None,
            "last_check_out": outs[-1] if outs else None,
            "latest_action": rows[-1][0] if rows else last_action_type,
            "latest_action_time": rows[-1][1] if rows else last_action_time_str,
            "cooldown_remaining_seconds": cooldown_remaining,
            "is_on_cooldown": cooldown_remaining > 0,
        }


def record_attendance_action(
    student_id: int,
    action: str,
    db_path: Path = DATABASE_PATH,
) -> tuple[bool, str, int, int]:
    """Record a check-in or check-out event enforcing the 1-hour rate limit across all actions.

    Only one action (either check-in or check-out) is allowed per hour per student.

    Returns:
        tuple[bool, str, int, int]: (success, message, current_action_count, remaining_cooldown_seconds)
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    iso_timestamp = now.isoformat()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # 1. Enforce 1-hour limit check: Query latest action across all logs for this student
        cursor.execute(
            """
            SELECT action, timestamp, date, time
            FROM attendance_logs
            WHERE student_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (student_id,),
        )
        last_row = cursor.fetchone()

        if last_row:
            last_action = last_row[0]
            dt = parse_db_timestamp(last_row[1], last_row[2], last_row[3])
            if dt:
                elapsed = (now - dt).total_seconds()
                if elapsed < ACTION_COOLDOWN_SECONDS:
                    remaining = int(ACTION_COOLDOWN_SECONDS - elapsed)
                    rem_m = remaining // 60
                    rem_s = remaining % 60
                    last_act_name = "Check-In" if last_action == ACTION_CHECK_IN else "Check-Out"
                    last_act_time = last_row[3]

                    # Get today's action count for context
                    cursor.execute(
                        "SELECT COUNT(*) FROM attendance_logs WHERE student_id = ? AND date = ? AND action = ?",
                        (student_id, date_str, action),
                    )
                    curr_count = cursor.fetchone()[0]

                    msg = (
                        f"Hourly limit active. Last {last_act_name} at {last_act_time}. "
                        f"Please wait {rem_m}m {rem_s}s before next action."
                    )
                    return False, msg, curr_count, remaining

        # 2. Insert into detailed audit event log
        cursor.execute(
            """
            INSERT INTO attendance_logs (student_id, action, date, time, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_id, action, date_str, time_str, iso_timestamp),
        )

        # 3. Count total actions of this type today
        cursor.execute(
            """
            SELECT COUNT(*) FROM attendance_logs
            WHERE student_id = ? AND date = ? AND action = ?
            """,
            (student_id, date_str, action),
        )
        action_count = cursor.fetchone()[0]

        # 4. Update/Insert summary in daily attendance table to maintain data consistency
        cursor.execute(
            """
            SELECT id, check_in_time, check_out_time FROM attendance
            WHERE student_id = ? AND date = ?
            """,
            (student_id, date_str),
        )
        row = cursor.fetchone()

        if action == ACTION_CHECK_IN:
            if row is None:
                cursor.execute(
                    """
                    INSERT INTO attendance (student_id, date, time, check_in_time, check_out_time, status)
                    VALUES (?, ?, ?, ?, NULL, 'CHECKED_IN')
                    """,
                    (student_id, date_str, time_str, time_str),
                )
            else:
                cursor.execute(
                    """
                    UPDATE attendance
                    SET check_in_time = ?, time = ?, status = 'CHECKED_IN'
                    WHERE student_id = ? AND date = ?
                    """,
                    (time_str, time_str, student_id, date_str),
                )
            conn.commit()
            msg = f"Check-In #{action_count} recorded at {time_str}"
            return True, msg, action_count, 0

        elif action == ACTION_CHECK_OUT:
            if row is None:
                cursor.execute(
                    """
                    INSERT INTO attendance (student_id, date, time, check_in_time, check_out_time, status)
                    VALUES (?, ?, ?, NULL, ?, 'CHECKED_OUT')
                    """,
                    (student_id, date_str, time_str, time_str),
                )
            else:
                cursor.execute(
                    """
                    UPDATE attendance
                    SET check_out_time = ?, status = 'CHECKED_OUT'
                    WHERE student_id = ? AND date = ?
                    """,
                    (time_str, student_id, date_str),
                )
            conn.commit()
            msg = f"Check-Out #{action_count} recorded at {time_str}"
            return True, msg, action_count, 0

        return False, "Unknown action", 0, 0
