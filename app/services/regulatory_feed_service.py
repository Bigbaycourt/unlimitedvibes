"""
Regulatory Feed Service

Monitors regulatory updates (FTC, GDPR, platform policies) and
assesses priority/relevance for creator compliance.
"""

from typing import List


class RegulatoryFeedService:
    """Monitor and prioritize regulatory updates for creator compliance."""

    # Keywords that indicate critical enforcement actions
    CRITICAL_KEYWORDS = ["fine", "penalty", "enforcement", "violation", "sued", "lawsuit"]

    # Keywords that indicate high-priority guidance changes
    HIGH_KEYWORDS = ["guidance", "guide", "update", "new rule", "proposed", "amendment"]

    # Keywords that indicate medium priority
    MEDIUM_KEYWORDS = ["review", "comment period", "draft", "notice"]

    def _assess_priority(
        self, content: str, keywords: List[str]
    ) -> str:
        """
        Assess the priority level of a regulatory update.

        Args:
            content: The regulatory update text
            keywords: Matched keywords from monitoring

        Returns:
            Priority level: "critical", "high", "medium", or "low"
        """
        content_lower = content.lower()

        # Check for critical indicators (enforcement actions, fines)
        for term in self.CRITICAL_KEYWORDS:
            if term in content_lower:
                return "critical"

        # Check for high-priority indicators (new guidance)
        for term in self.HIGH_KEYWORDS:
            if term in content_lower:
                return "high"

        # Check for medium indicators
        for term in self.MEDIUM_KEYWORDS:
            if term in content_lower:
                return "medium"

        return "low"

    def _match_keywords(
        self, content: str, keywords: List[str]
    ) -> List[str]:
        """
        Match keywords against content using root/stem matching.

        Uses prefix matching for longer keywords to catch variations
        (e.g., "disclosure" matches "undisclosed", "disclosed", etc.)

        Args:
            content: Text to search in
            keywords: Keywords to match

        Returns:
            List of matched keywords
        """
        content_lower = content.lower()
        matched = []

        for kw in keywords:
            kw_lower = kw.lower()
            # For longer keywords, use prefix/root matching
            # to catch variations (e.g., "disclos" matches "undisclosed")
            if len(kw_lower) > 4:
                check = kw_lower[: min(len(kw_lower), 6)]
            else:
                check = kw_lower

            if check in content_lower:
                matched.append(kw)

        return matched
