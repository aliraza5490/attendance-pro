"""Activity and Audit Logs router."""

from typing import List, Optional
from fastapi import APIRouter, Query

from app.database import get_activity_logs
from app.schemas import ActivityLog

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=List[ActivityLog])
def list_logs(
    limit: int = Query(50, ge=1, le=200),
    date: Optional[str] = Query(None, description="Filter logs by date (YYYY-MM-DD)"),
    action: Optional[str] = Query(None, description="Filter logs by action (CHECK_IN, CHECK_OUT)"),
):
    """Retrieve audit activity logs."""
    return get_activity_logs(limit=limit, date_filter=date, action_filter=action)
