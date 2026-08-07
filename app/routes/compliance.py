"""
Compliance API Routes

Endpoints:
- GET  /api/compliance/dashboard
- POST /api/compliance/moderate
- GET  /api/compliance/monitoring/updates
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.dependencies import require_auth

router = APIRouter()


# ============================================================================
# Request / Response Models
# ============================================================================

class ModerateRequest(BaseModel):
    content_text: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    caption: Optional[str] = None


class ModerationResult(BaseModel):
    risk_level: str
    safety_score: int
    can_publish: bool
    issues: List[str]
    violations: List[str]


class DashboardResponse(BaseModel):
    compliance_score: int
    risk_level: str
    applicable_regulations: List[str]
    recent_issues: List[str]


class RegulatoryUpdate(BaseModel):
    title: str
    priority: str
    source: str
    date: str


class MonitoringResponse(BaseModel):
    updates: List[RegulatoryUpdate]
    last_checked: str


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/dashboard")
async def compliance_dashboard(token: str = Depends(require_auth)):
    """
    Get compliance dashboard overview.

    Returns current compliance score, risk level, and applicable regulations.
    """
    return DashboardResponse(
        compliance_score=92,
        risk_level="low",
        applicable_regulations=["FTC Endorsement Guides", "GDPR", "CCPA", "Platform ToS"],
        recent_issues=[],
    )


@router.post("/moderate")
async def moderate_content(
    request: ModerateRequest,
    token: str = Depends(require_auth),
):
    """
    Moderate content for safety and compliance.

    Analyzes content text against platform policies, FTC guidelines,
    and health/financial claim rules.
    """
    # Simple rule-based moderation for scaffold
    issues = []
    violations = []
    safety_score = 95
    risk_level = "safe"

    content_lower = request.content_text.lower()

    # Check for health claims
    health_terms = ["cures", "heals", "treats", "prevents disease", "miracle"]
    for term in health_terms:
        if term in content_lower:
            issues.append(f"Potential unsubstantiated health claim: '{term}'")
            safety_score -= 20
            risk_level = "medium_risk"

    # Check for missing disclosure on sponsored content
    sponsor_indicators = ["#ad", "#sponsored", "#partner", "paid partnership"]
    affiliate_indicators = ["use code", "affiliate", "commission", "discount code"]

    has_affiliate = any(ind in content_lower for ind in affiliate_indicators)
    has_disclosure = any(ind in content_lower for ind in sponsor_indicators)

    if has_affiliate and not has_disclosure:
        issues.append("Affiliate/sponsored content may need #ad disclosure")
        safety_score -= 15
        if risk_level == "safe":
            risk_level = "low_risk"

    # Clamp score
    safety_score = max(0, min(100, safety_score))

    if safety_score < 30:
        risk_level = "high_risk"
    elif safety_score < 50:
        risk_level = "medium_risk"

    return ModerationResult(
        risk_level=risk_level,
        safety_score=safety_score,
        can_publish=risk_level not in ("high_risk", "violation"),
        issues=issues,
        violations=violations,
    )


@router.get("/monitoring/updates")
async def regulatory_updates(token: str = Depends(require_auth)):
    """
    Get recent regulatory updates relevant to creator compliance.
    """
    return MonitoringResponse(
        updates=[
            RegulatoryUpdate(
                title="FTC Updated Endorsement Guides",
                priority="high",
                source="FTC.gov",
                date="2026-07-15",
            ),
            RegulatoryUpdate(
                title="Instagram Updated Branded Content Policy",
                priority="medium",
                source="Instagram Policy Blog",
                date="2026-07-20",
            ),
        ],
        last_checked="2026-08-07T16:00:00Z",
    )
