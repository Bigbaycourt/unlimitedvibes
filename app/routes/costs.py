"""
Cost Optimization API Routes

Endpoints:
- GET /api/costs/usage
- GET /api/costs/forecast
- GET /api/costs/competitive-analysis
"""

from fastapi import APIRouter, Depends
from decimal import Decimal

from app.dependencies import require_admin
from app.services.cost_optimization_service import CostOptimizationService

router = APIRouter()


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/usage")
async def get_usage(token: str = Depends(require_admin)):
    """
    Get current month's API usage and costs.

    Requires admin access.
    """
    service = CostOptimizationService()

    # Simulated current month usage
    estimate = service.calculate_monthly_cost_estimate(
        input_tokens=2_500_000,
        output_tokens=350_000,
        model="claude-sonnet-4",
        use_batch_api=False,
    )

    return {
        "monthly_cost": float(estimate["monthly_cost_usd"]),
        "total_usage": {
            "input_tokens": 2_500_000,
            "output_tokens": 350_000,
        },
        "model": "claude-sonnet-4",
        "billing_period": "2026-08",
    }


@router.get("/forecast")
async def get_forecast(token: str = Depends(require_admin)):
    """
    Get 12-month cost forecast.

    Requires admin access.
    """
    service = CostOptimizationService()

    base_monthly = service.calculate_monthly_cost_estimate(
        input_tokens=2_500_000,
        output_tokens=350_000,
        model="claude-sonnet-4",
        use_batch_api=False,
    )["monthly_cost_usd"]

    # 5% monthly growth projection
    monthly_forecasts = []
    total_annual = Decimal("0")

    for month in range(12):
        growth_factor = Decimal(str(1.05 ** month))
        month_cost = base_monthly * growth_factor
        total_annual += month_cost
        monthly_forecasts.append({
            "month": month + 1,
            "projected_cost_usd": float(round(month_cost, 2)),
        })

    return {
        "forecast": monthly_forecasts,
        "projected_annual_cost": float(round(total_annual, 2)),
        "growth_rate_pct": 5,
        "model": "claude-sonnet-4",
    }


@router.get("/competitive-analysis")
async def get_competitive_analysis(token: str = Depends(require_admin)):
    """
    Compare current costs to competitor pricing.

    Requires admin access.
    """
    service = CostOptimizationService()

    comparison = service.compare_to_competitors(
        input_tokens=2_500_000,
        output_tokens=350_000,
    )

    providers = {}
    for provider, data in comparison.items():
        providers[provider] = {
            "estimated_cost_usd": float(data["estimated_cost_usd"]),
        }

    return {
        "providers": providers,
        "token_volume": {
            "input_tokens": 2_500_000,
            "output_tokens": 350_000,
        },
    }
