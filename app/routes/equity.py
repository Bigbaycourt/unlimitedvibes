"""
Equity API Routes

Endpoints:
- GET /api/equity/cap-table
- GET /api/equity/positions
- GET /api/equity/dilution-analysis
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

from app.dependencies import require_admin

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class CapTableResponse(BaseModel):
    company_id: str
    authorized_shares: int
    common_shares_issued: int
    preferred_shares_issued: int
    option_pool_total: int
    option_pool_granted: int
    option_pool_available: int
    warrant_shares: int
    fully_diluted_shares: int
    current_valuation_usd: int
    current_round_name: str
    founder_ownership_pct: float


class PositionResponse(BaseModel):
    holder_name: str
    holder_type: str
    equity_type: str
    shares_owned: int
    ownership_pct: float
    fully_diluted_pct: float
    note: Optional[str] = None


class DilutionAnalysisResponse(BaseModel):
    dilution_analysis: dict


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/cap-table")
async def get_cap_table(token: str = Depends(require_admin)):
    """
    Get current cap table snapshot.

    Requires admin access.
    """
    return CapTableResponse(
        company_id="unlimitedvibes",
        authorized_shares=10_000_000,
        common_shares_issued=1_000_000,
        preferred_shares_issued=0,
        option_pool_total=200_000,
        option_pool_granted=50_000,
        option_pool_available=150_000,
        warrant_shares=0,
        fully_diluted_shares=1_200_000,
        current_valuation_usd=5_000_000,
        current_round_name="Pre-seed",
        founder_ownership_pct=83.3,
    )


@router.get("/positions")
async def get_positions(token: str = Depends(require_admin)):
    """
    Get all equity positions.

    Requires admin access.
    """
    return {
        "positions": [
            PositionResponse(
                holder_name="Antavis Foreman",
                holder_type="founder",
                equity_type="common",
                shares_owned=800_000,
                ownership_pct=80.0,
                fully_diluted_pct=66.7,
                note="CEO & Founder",
            ).model_dump(),
            PositionResponse(
                holder_name="Option Pool",
                holder_type="pool",
                equity_type="options",
                shares_owned=200_000,
                ownership_pct=20.0,
                fully_diluted_pct=16.7,
                note="Employee option pool",
            ).model_dump(),
        ]
    }


@router.get("/dilution-analysis")
async def dilution_analysis(
    future_round_amount: float = Query(..., gt=0),
    share_price: float = Query(..., gt=0),
    token: str = Depends(require_admin),
):
    """
    Analyze dilution impact of a future funding round.

    Requires admin access.
    """
    # Current state
    current_fd = 1_200_000
    current_founder_shares = 800_000
    founder_pct_before = (current_founder_shares / current_fd) * 100

    # New shares from round
    new_shares = int(future_round_amount / share_price)
    post_fd = current_fd + new_shares
    founder_pct_after = (current_founder_shares / post_fd) * 100

    return {
        "dilution_analysis": {
            "founder_ownership_pct_before": round(founder_pct_before, 2),
            "founder_ownership_pct_after": round(founder_pct_after, 2),
            "dilution_pct": round(founder_pct_before - founder_pct_after, 2),
            "new_shares_issued": new_shares,
            "post_money_fd_shares": post_fd,
            "investment_amount": future_round_amount,
            "share_price": share_price,
        }
    }
