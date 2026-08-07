"""
Compliance Scoring Service

Scores creator compliance based on post history:
- Sponsorship disclosure (40 pts)
- Platform flags (30 pts)
- AI content disclosure (20 pts)
- Base/recency (10 pts)

Total: 100 points max
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class PostComplianceRecord:
    """Record of a single post's compliance status."""

    post_id: str
    platform: str
    posted_at: datetime
    is_sponsored: bool
    has_disclosure_tag: bool
    was_flagged_by_platform: bool
    ai_generated: bool
    ai_disclosure_present: bool


class ComplianceScorer:
    """
    Calculate a compliance score (0-100) from post history.

    Breakdown:
    - sponsorship_disclosure: 40 pts (proper #ad/#sponsored tagging)
    - platform_flags: 30 pts (no platform violations)
    - ai_disclosure: 20 pts (AI-generated content properly labeled)
    - base: 10 pts (baseline)
    """

    MAX_SPONSORSHIP_SCORE = 40
    MAX_PLATFORM_SCORE = 30
    MAX_AI_SCORE = 20
    MAX_BASE_SCORE = 10

    def calculate_score(self, posts: List[PostComplianceRecord]) -> Dict[str, Any]:
        """
        Calculate overall compliance score from post history.

        Args:
            posts: List of PostComplianceRecord entries

        Returns:
            dict with score, confidence, reason, breakdown
        """
        if not posts:
            return {
                "score": 100,
                "confidence": "low",
                "reason": "No post history available",
                "breakdown": {
                    "sponsorship_disclosure": self.MAX_SPONSORSHIP_SCORE,
                    "platform_flags": self.MAX_PLATFORM_SCORE,
                    "ai_disclosure": self.MAX_AI_SCORE,
                    "base": self.MAX_BASE_SCORE,
                },
            }

        # --- Sponsorship disclosure score (40 pts) ---
        sponsored_posts = [p for p in posts if p.is_sponsored]
        if sponsored_posts:
            disclosed_count = sum(1 for p in sponsored_posts if p.has_disclosure_tag)
            sponsorship_score = int(
                (disclosed_count / len(sponsored_posts)) * self.MAX_SPONSORSHIP_SCORE
            )
        else:
            sponsorship_score = self.MAX_SPONSORSHIP_SCORE

        # --- Platform flags score (30 pts) ---
        # Weighted by recency: recent flags hurt more
        now = datetime.utcnow()
        flag_penalty = 0.0
        for p in posts:
            if p.was_flagged_by_platform:
                days_old = max(0, (now - p.posted_at).days)
                recency_weight = max(0.1, 1.0 - days_old / 90.0)
                flag_penalty += recency_weight * (self.MAX_PLATFORM_SCORE / len(posts))
        platform_score = max(0, int(self.MAX_PLATFORM_SCORE - flag_penalty))

        # --- AI disclosure score (20 pts) ---
        ai_posts = [p for p in posts if p.ai_generated]
        if ai_posts:
            ai_disclosed_count = sum(1 for p in ai_posts if p.ai_disclosure_present)
            ai_score = int(
                (ai_disclosed_count / len(ai_posts)) * self.MAX_AI_SCORE
            )
        else:
            ai_score = self.MAX_AI_SCORE

        # --- Base score (10 pts) ---
        base_score = self.MAX_BASE_SCORE

        # --- Total ---
        total = min(
            100,
            sponsorship_score + platform_score + ai_score + base_score,
        )

        # Confidence based on sample size
        if len(posts) >= 10:
            confidence = "high"
        elif len(posts) >= 5:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "score": total,
            "confidence": confidence,
            "reason": self._build_reason(sponsorship_score, platform_score, ai_score),
            "breakdown": {
                "sponsorship_disclosure": sponsorship_score,
                "platform_flags": platform_score,
                "ai_disclosure": ai_score,
                "base": base_score,
            },
        }

    def _build_reason(self, sponsorship: int, platform: int, ai: int) -> str:
        """Generate human-readable reason string."""
        issues = []
        if sponsorship < self.MAX_SPONSORSHIP_SCORE:
            issues.append("missing sponsorship disclosures")
        if platform < self.MAX_PLATFORM_SCORE:
            issues.append("platform policy flags")
        if ai < self.MAX_AI_SCORE:
            issues.append("missing AI content labels")

        if not issues:
            return "Full compliance across all categories"
        return "Score reduced due to: " + ", ".join(issues)
