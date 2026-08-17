"""Pydantic schemas for the Attendance Backend API."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# Student Schemas
# ==============================================================================

class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class StudentCreate(StudentBase):
    id: Optional[int] = None


class StudentResponse(StudentBase):
    id: int
    total_attendances: int = 0
    last_attended_date: Optional[str] = None
    attendance_rate: float = 0.0


# ==============================================================================
# Attendance Schemas
# ==============================================================================

class AttendanceRecord(BaseModel):
    id: int
    student_id: int
    student_name: str
    date: str
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    status: Optional[str] = None


class AttendanceListResponse(BaseModel):
    records: List[AttendanceRecord]
    total_count: int
    page: int
    page_size: int


class ManualAttendanceAction(BaseModel):
    student_id: int
    action: str = Field(..., pattern="^(CHECK_IN|CHECK_OUT)$")
    date: Optional[str] = None
    time: Optional[str] = None


# ==============================================================================
# Activity Log Schemas
# ==============================================================================

class ActivityLog(BaseModel):
    id: int
    student_id: int
    student_name: str
    action: str
    date: str
    time: str
    timestamp: str


# ==============================================================================
# Analytics Schemas
# ==============================================================================

class SummaryMetrics(BaseModel):
    total_students: int
    present_today: int
    checked_in_now: int
    checked_out_today: int
    absent_today: int
    attendance_rate: float
    today_logs_count: int
    today_date: str


class DayTrend(BaseModel):
    date: str
    day_name: str
    present: int
    checked_out: int
    total_students: int
    rate: float


class HourlyCount(BaseModel):
    hour: str
    check_ins: int
    check_outs: int
