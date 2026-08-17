"""Attendance router for retrieving and updating attendance records."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.database import get_attendance_records, record_manual_attendance
from app.schemas import AttendanceListResponse, ManualAttendanceAction

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.get("", response_model=AttendanceListResponse)
def list_attendance(
    date: Optional[str] = Query(None, description="Date filter (YYYY-MM-DD)"),
    student_id: Optional[int] = Query(None, description="Filter by Student ID"),
    status: Optional[str] = Query(None, description="Filter by status (CHECKED_IN, CHECKED_OUT)"),
    search: Optional[str] = Query(None, description="Search student name or ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Retrieve filtered and paginated attendance records."""
    offset = (page - 1) * page_size
    records, total_count = get_attendance_records(
        date_filter=date,
        student_id=student_id,
        status_filter=status,
        search=search,
        limit=page_size,
        offset=offset,
    )
    return {
        "records": records,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/today")
def today_attendance():
    """Shortcut to get today's attendance records."""
    from datetime import date
    today_str = date.today().isoformat()
    records, total = get_attendance_records(date_filter=today_str, limit=100)
    return {"records": records, "total_count": total}


@router.post("/manual", status_code=status.HTTP_200_OK)
def manual_action(payload: ManualAttendanceAction):
    """Record manual check-in or check-out for a student."""
    try:
        result = record_manual_attendance(
            student_id=payload.student_id,
            action=payload.action,
            action_date=payload.date,
            action_time=payload.time,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
