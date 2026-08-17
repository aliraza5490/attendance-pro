"""Analytics router for summary metrics and attendance trends."""

from typing import List, Optional
from fastapi import APIRouter, Query

from app.database import get_hourly_distribution, get_summary_metrics, get_weekly_trend
from app.schemas import DayTrend, HourlyCount, SummaryMetrics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=SummaryMetrics)
def summary():
    """Get real-time summary KPIs for today."""
    return get_summary_metrics()


@router.get("/weekly", response_model=List[DayTrend])
def weekly(days: int = Query(7, ge=1, le=30)):
    """Get daily attendance trends over the last N days."""
    return get_weekly_trend(days=days)


@router.get("/hourly", response_model=List[HourlyCount])
def hourly(date: Optional[str] = Query(None, description="YYYY-MM-DD")):
    """Get check-in & check-out volume grouped by hour."""
    return get_hourly_distribution(target_date=date)
