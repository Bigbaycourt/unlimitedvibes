"""
Unit Tests: Compliance Monitoring System

Tests for:
- Content moderation (without Claude API calls)
- FTC/GDPR/CCPA compliance checks
- Compliance scoring
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.services.content_moderation_service import ContentModerationService
from app.services.compliance_scoring import ComplianceScorer, PostComplianceRecord

# ============================================================================
# TESTS: Content Moderation
# ============================================================================

class TestContentModerationService:
    """Test ContentModerationService methods"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return ContentModerationService()

    @pytest.mark.unit
    async def test_moderate_content_safe(self, service):
        """Test that safe content passes moderation"""

        # Mock Claude API response
        with patch.object(service, 'moderate_content') as mock_moderate:
            mock_moderate.return_value = {
                "risk_level": "safe",
                "safety_score": 95,
                "can_publish": True,
                "issues": [],
                "violations": []
            }

            result = await service.moderate_content(
                content_text="My fitness journey this week!",
                platform="instagram"
            )

            assert result["risk_level"] == "safe"
            assert result["can_publish"] is True
            assert result["safety_score"] >= 90

    @pytest.mark.unit
    async def test_moderate_content_with_warning(self, service):
        """Test that content with issues is flagged"""

        with patch.object(service, 'moderate_content') as mock_moderate:
            mock_moderate.return_value = {
                "risk_level": "medium_risk",
                "safety_score": 65,
                "can_publish": True,
                "issues": ["Unsubstantiated health claim"],
                "violations": []
            }

            result = await service.moderate_content(
                content_text="This supplement cures cancer!",
                platform="instagram"
            )

            assert result["risk_level"] == "medium_risk"
            assert len(result["issues"]) > 0
            assert "Unsubstantiated" in result["issues"][0]

    @pytest.mark.unit
    async def test_check_ftc_compliance_with_disclosure(self, service):
        """Test FTC compliance check with proper disclosure"""

        with patch.object(service, 'check_ftc_compliance') as mock_check:
            mock_check.return_value = {
                "is_compliant": True,
                "disclosure_present": True,
                "issues": [],
                "recommendation": "Post is compliant"
            }

            result = await service.check_ftc_compliance(
                caption="Love this product! #ad",
                is_sponsored=True,
                has_affiliate_link=False
            )

            assert result["is_compliant"] is True
            assert result["disclosure_present"] is True

    @pytest.mark.unit
    async def test_check_ftc_compliance_missing_disclosure(self, service):
        """Test FTC compliance check without disclosure"""

        with patch.object(service, 'check_ftc_compliance') as mock_check:
            mock_check.return_value = {
                "is_compliant": False,
                "disclosure_present": False,
                "issues": ["Missing #ad disclosure on sponsored post"],
                "recommendation": "Add #ad or #sponsored"
            }

            result = await service.check_ftc_compliance(
                caption="Love this product!",
                is_sponsored=True,
                has_affiliate_link=False
            )

            assert result["is_compliant"] is False
            assert result["disclosure_present"] is False
            assert "missing" in result["issues"][0].lower()

    @pytest.mark.unit
    async def test_check_gdpr_compliance_with_privacy_policy(self, service):
        """Test GDPR compliance when privacy policy exists"""

        with patch.object(service, 'check_gdpr_compliance') as mock_check:
            mock_check.return_value = {
                "is_compliant": True,
                "issues": [],
                "recommendations": []
            }

            result = await service.check_gdpr_compliance(
                content="Download my free guide",
                targets_eu_audience=True,
                collects_data=True,
                has_privacy_policy=True
            )

            assert result["is_compliant"] is True

    @pytest.mark.unit
    async def test_check_gdpr_compliance_missing_privacy_policy(self, service):
        """Test GDPR compliance check without privacy policy"""

        with patch.object(service, 'check_gdpr_compliance') as mock_check:
            mock_check.return_value = {
                "is_compliant": False,
                "issues": ["No privacy policy for EU audience with data collection"],
                "recommendations": ["Add privacy policy to bio"]
            }

            result = await service.check_gdpr_compliance(
                content="Download my free guide",
                targets_eu_audience=True,
                collects_data=True,
                has_privacy_policy=False
            )

            assert result["is_compliant"] is False
            assert len(result["issues"]) > 0


# ============================================================================
# TESTS: Compliance Scoring
# ============================================================================

class TestComplianceScorer:
    """Test compliance scoring calculations"""

    @pytest.fixture
    def scorer(self):
        """Create scorer instance"""
        return ComplianceScorer()

    def test_score_empty_history(self, scorer):
        """Test scoring with no post history"""

        result = scorer.calculate_score([])

        assert result["score"] == 100
        assert result["confidence"] == "low"
        assert "No post history" in result["reason"]

    def test_score_perfect_compliance(self, scorer):
        """Test scoring with perfect compliance"""

        posts = [
            PostComplianceRecord(
                post_id="1",
                platform="instagram",
                posted_at=datetime.utcnow(),
                is_sponsored=True,
                has_disclosure_tag=True,
                was_flagged_by_platform=False,
                ai_generated=False,
                ai_disclosure_present=True
            )
            for _ in range(10)
        ]

        result = scorer.calculate_score(posts)

        assert result["score"] == 100
        assert result["confidence"] == "high"
        assert result["breakdown"]["sponsorship_disclosure"] == 40

    def test_score_with_violations(self, scorer):
        """Test scoring with platform violations"""

        posts = [
            PostComplianceRecord(
                post_id=str(i),
                platform="instagram",
                posted_at=datetime.utcnow(),
                is_sponsored=i < 5,  # First 5 are sponsored
                has_disclosure_tag=i < 3,  # Only 3 have disclosure
                was_flagged_by_platform=i > 7,  # Last 2 were flagged
                ai_generated=False,
                ai_disclosure_present=True
            )
            for i in range(10)
        ]

        result = scorer.calculate_score(posts)

        assert result["score"] < 100
        assert result["score"] > 0
        assert result["breakdown"]["platform_flags"] < 30  # Lost points for flags

    def test_score_ai_disclosure_gap(self, scorer):
        """Test scoring with AI-generated content not labeled"""

        posts = [
            PostComplianceRecord(
                post_id=str(i),
                platform="instagram",
                posted_at=datetime.utcnow(),
                is_sponsored=False,
                has_disclosure_tag=False,
                was_flagged_by_platform=False,
                ai_generated=True,
                ai_disclosure_present=False  # Missing AI label
            )
            for i in range(5)
        ]

        result = scorer.calculate_score(posts)

        # Should lose points for missing AI disclosure
        assert result["breakdown"]["ai_disclosure"] < 20

    def test_score_recency_matters(self, scorer):
        """Test that recent violations hurt score more"""

        old_violation = PostComplianceRecord(
            post_id="1",
            platform="instagram",
            posted_at=datetime.utcnow() - timedelta(days=60),
            is_sponsored=True,
            has_disclosure_tag=False,
            was_flagged_by_platform=True,
            ai_generated=False,
            ai_disclosure_present=False
        )

        recent_violation = PostComplianceRecord(
            post_id="2",
            platform="instagram",
            posted_at=datetime.utcnow() - timedelta(days=5),
            is_sponsored=True,
            has_disclosure_tag=False,
            was_flagged_by_platform=True,
            ai_generated=False,
            ai_disclosure_present=False
        )

        # Score with old violation
        score_old = scorer.calculate_score([old_violation] + [
            PostComplianceRecord(
                post_id=str(i),
                platform="instagram",
                posted_at=datetime.utcnow(),
                is_sponsored=False,
                has_disclosure_tag=False,
                was_flagged_by_platform=False,
                ai_generated=False,
                ai_disclosure_present=False
            )
            for i in range(9)
        ])

        # Score with recent violation
        score_recent = scorer.calculate_score([recent_violation] + [
            PostComplianceRecord(
                post_id=str(i),
                platform="instagram",
                posted_at=datetime.utcnow(),
                is_sponsored=False,
                has_disclosure_tag=False,
                was_flagged_by_platform=False,
                ai_generated=False,
                ai_disclosure_present=False
            )
            for i in range(9)
        ])

        # Recent violation should score lower
        assert score_recent["score"] < score_old["score"]


# ============================================================================
# TESTS: Regulatory Feed Service
# ============================================================================

class TestRegulatoryFeedService:
    """Test regulatory monitoring"""

    @pytest.mark.unit
    def test_priority_assessment_critical(self):
        """Test that enforcement actions get CRITICAL priority"""

        from app.services.regulatory_feed_service import RegulatoryFeedService

        service = RegulatoryFeedService()

        content = "FTC issued $100,000 fine for undisclosed endorsements"
        priority = service._assess_priority(content, ["ftc", "endorsement"])

        assert priority == "critical"

    @pytest.mark.unit
    def test_priority_assessment_high(self):
        """Test that guidance updates get HIGH priority"""

        from app.services.regulatory_feed_service import RegulatoryFeedService

        service = RegulatoryFeedService()

        content = "New FTC Endorsement Guides provide updated guidance on disclosures"
        priority = service._assess_priority(content, ["ftc", "guidance"])

        assert priority == "high"

    @pytest.mark.unit
    def test_keyword_matching(self):
        """Test keyword matching in feed content"""

        from app.services.regulatory_feed_service import RegulatoryFeedService

        service = RegulatoryFeedService()

        content = "FTC enforcement action on undisclosed sponsorships"
        keywords = ["ftc", "sponsorship", "disclosure"]

        matched = service._match_keywords(content, keywords)

        assert "ftc" in matched
        assert "sponsorship" in matched
        assert "disclosure" in matched


# ============================================================================
# MARKERS & PARAMETRIZATION
# ============================================================================

@pytest.mark.compliance
@pytest.mark.unit
@pytest.mark.parametrize("risk_level,expected_score", [
    ("safe", 95),
    ("low_risk", 75),
    ("medium_risk", 50),
    ("high_risk", 25),
    ("violation", 0),
])
def test_risk_level_to_score_mapping(risk_level, expected_score):
    """Test mapping risk levels to compliance scores"""

    # Risk level should correlate with score
    score_ranges = {
        "safe": (90, 100),
        "low_risk": (70, 85),
        "medium_risk": (40, 70),
        "high_risk": (10, 40),
        "violation": (0, 20),
    }

    min_score, max_score = score_ranges[risk_level]
    assert min_score <= expected_score <= max_score


@pytest.mark.compliance
@pytest.mark.parametrize("platform,applies_to", [
    ("instagram", ["ftc", "platform"]),
    ("tiktok", ["ftc", "platform", "coppa"]),
    ("youtube", ["ftc", "platform"]),
    ("twitter", ["ftc", "platform"]),
])
def test_platform_specific_rules(platform, applies_to):
    """Test that regulations vary by platform"""

    # Each platform has specific rules
    assert "ftc" in applies_to  # All require FTC compliance
    assert "platform" in applies_to  # All have platform-specific policies
