"""Dashboard statistics API routes (FastAPI)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth.dependencies import get_current_user
from backend.controller.stats_controller import StatsController
from backend.core.request_context import CurrentUser

router = APIRouter(prefix="/api/stats", tags=["Dashboard Stats"])
_controller = StatsController()


@router.get("/dashboard")
def dashboard(_user: CurrentUser = Depends(get_current_user)):
    """Live dashboard overview metrics."""
    return _controller.dashboard()


@router.get("/charts")
def charts(_user: CurrentUser = Depends(get_current_user)):
    """Chart.js datasets."""
    return _controller.charts()


@router.get("/alerts")
def alerts(_user: CurrentUser = Depends(get_current_user)):
    """Clinical alert feed."""
    return _controller.alerts()


@router.get("/patients")
def patients(_user: CurrentUser = Depends(get_current_user)):
    """Patient statistics."""
    return _controller.patients()


@router.get("/ai-performance")
def ai_performance(_user: CurrentUser = Depends(get_current_user)):
    """AI performance KPIs."""
    return _controller.ai_performance()
