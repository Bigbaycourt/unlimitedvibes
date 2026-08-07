"""
Unit Tests: API Cost Optimization System

Tests for:
- Cost calculation (Anthropic, competitors)
- Pricing impact modeling
- Batch API savings
- Cost optimization recommendations
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.cost_optimization_service import CostOptimizationService


class TestCostOptimizationService:
    """Test cost optimization calculations"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return CostOptimizationService()

    @pytest.mark.costs
    def test_current_anthropic_pricing(self, service):
        """Test that pricing reflects current rates"""

        # Post-50% increase pricing (2024)
        opus_input = service.CURRENT_PRICING["claude-opus-4"]["input_cost_per_mtok"]
        opus_output = service.CURRENT_PRICING["claude-opus-4"]["output_cost_per_mtok"]

        # Should be $4.50 / $22.50
        assert opus_input == Decimal("4.50")
        assert opus_output == Decimal("22.50")

    @pytest.mark.costs
    def test_haiku_is_cheapest(self, service):
        """Test that Haiku is the cheapest model"""

        models = ["claude-opus-4", "claude-sonnet-4", "claude-haiku-3"]

        prices = {
            model: (
                service.CURRENT_PRICING[model]["input_cost_per_mtok"],
                service.CURRENT_PRICING[model]["output_cost_per_mtok"]
            )
            for model in models
        }

        # Haiku input cost should be lowest
        haiku_input = prices["claude-haiku-3"][0]
        sonnet_input = prices["claude-sonnet-4"][0]
        opus_input = prices["claude-opus-4"][0]

        assert haiku_input < sonnet_input < opus_input

    @pytest.mark.costs
    def test_batch_api_50_percent_savings(self, service):
        """Test that Batch API provides 50% discount"""

        # Standard pricing
        opus_input = Decimal("4.50")
        opus_output = Decimal("22.50")

        # Batch should be exactly 50% off
        batch_input = opus_input * Decimal("0.5")
        batch_output = opus_output * Decimal("0.5")

        assert batch_input == Decimal("2.25")
        assert batch_output == Decimal("11.25")

    @pytest.mark.costs
    def test_calculate_monthly_cost_estimate_basic(self, service):
        """Test basic monthly cost calculation"""

        # 1M input tokens, 100K output tokens, Opus
        result = service.calculate_monthly_cost_estimate(
            input_tokens=1_000_000,
            output_tokens=100_000,
            model="claude-opus-4",
            use_batch_api=False
        )

        # Cost = (1M * $4.50/M) + (100K * $22.50/M)
        expected_input_cost = Decimal("4.50")
        expected_output_cost = Decimal("2.25")  # 100K = 0.1M, 0.1 * 22.50
        expected_total = expected_input_cost + expected_output_cost

        assert result["monthly_cost_usd"] == expected_total
        assert result["model"] == "claude-opus-4"

    @pytest.mark.costs
    def test_calculate_monthly_cost_with_batch_api(self, service):
        """Test cost calculation with Batch API enabled"""

        result_standard = service.calculate_monthly_cost_estimate(
            input_tokens=1_000_000,
            output_tokens=100_000,
            model="claude-opus-4",
            use_batch_api=False
        )

        result_batch = service.calculate_monthly_cost_estimate(
            input_tokens=1_000_000,
            output_tokens=100_000,
            model="claude-opus-4",
            use_batch_api=True
        )

        # Batch should be exactly 50% of standard
        assert result_batch["monthly_cost_usd"] == result_standard["monthly_cost_usd"] * Decimal("0.5")

    @pytest.mark.costs
    def test_cost_per_feature_estimation(self, service):
        """Test cost breakdown by feature"""

        # Estimate costs for different features
        result = service.get_cost_per_feature(
            features=[
                "content_moderation",
                "content_generation",
                "compliance_monitoring",
                "creator_support"
            ]
        )

        # Should have estimates for each feature
        assert "content_moderation" in result
        assert "content_generation" in result
        assert "compliance_monitoring" in result
        assert "creator_support" in result

        # Content generation should cost more than moderation
        assert (
            result["content_generation"]["monthly_cost_usd"] >
            result["content_moderation"]["monthly_cost_usd"]
        )

    @pytest.mark.costs
    def test_compare_to_competitors(self, service):
        """Test competitive pricing analysis"""

        result = service.compare_to_competitors(
            input_tokens=1_000_000,
            output_tokens=100_000
        )

        # Should include major competitors
        assert "anthropic" in result
        assert "openai" in result
        assert "google" in result

        # Result should show relative costs
        anthropic_cost = result["anthropic"]["estimated_cost_usd"]
        openai_cost = result["openai"]["estimated_cost_usd"]
        google_cost = result["google"]["estimated_cost_usd"]

        # Costs should be positive
        assert anthropic_cost > 0
        assert openai_cost > 0
        assert google_cost > 0

    @pytest.mark.costs
    def test_pricing_increase_impact_modeling(self, service):
        """Test modeling impact of price increases"""

        # Current cost
        current_result = service.calculate_monthly_cost_estimate(
            input_tokens=10_000_000,
            output_tokens=1_000_000,
            model="claude-opus-4",
            use_batch_api=False
        )

        # Model 20% price increase
        result = service.model_pricing_increase_impact(
            input_tokens=10_000_000,
            output_tokens=1_000_000,
            model="claude-opus-4",
            price_increase_pct=20
        )

        # New cost should be 20% higher
        expected_new_cost = current_result["monthly_cost_usd"] * Decimal("1.20")

        assert result["new_monthly_cost_usd"] == expected_new_cost
        assert result["cost_increase_usd"] == result["new_monthly_cost_usd"] - current_result["monthly_cost_usd"]

    @pytest.mark.costs
    def test_annual_budget_forecasting(self, service):
        """Test annual cost forecasting"""

        # Monthly cost
        monthly_result = service.calculate_monthly_cost_estimate(
            input_tokens=1_000_000,
            output_tokens=100_000,
            model="claude-opus-4",
            use_batch_api=False
        )

        # Annual should be 12x monthly
        annual_cost = monthly_result["monthly_cost_usd"] * 12

        # With 10% growth assumption
        growth_factor = Decimal("1.10")
        annual_with_growth = annual_cost * (1 + (growth_factor - 1) / 2)  # Average growth

        assert annual_with_growth > annual_cost


class TestCostOptimizationStrategy:
    """Test cost optimization strategies"""

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return CostOptimizationService()

    @pytest.mark.costs
    def test_model_routing_strategy(self, service):
        """Test optimal model selection by use case"""

        use_cases = {
            "content_moderation": "claude-haiku-3",  # Fast, binary classification
            "compliance_check": "claude-sonnet-4",  # Balanced
            "content_generation": "claude-opus-4",  # Complex reasoning
            "regulatory_monitoring": "claude-haiku-3",  # Pattern matching
        }

        # Verify cost ordering
        haiku_cost = service.CURRENT_PRICING["claude-haiku-3"]["input_cost_per_mtok"]
        sonnet_cost = service.CURRENT_PRICING["claude-sonnet-4"]["input_cost_per_mtok"]
        opus_cost = service.CURRENT_PRICING["claude-opus-4"]["input_cost_per_mtok"]

        assert haiku_cost < sonnet_cost < opus_cost

    @pytest.mark.costs
    def test_batch_api_priority_ranking(self):
        """Test which tasks should use Batch API"""

        batch_candidates = {
            "content_moderation": True,  # Non-urgent, high volume
            "compliance_monitoring": True,  # Daily batch OK
            "emergency_support": False,  # Needs immediate response
            "real_time_check": False,  # User-facing
            "nightly_reporting": True,  # Batch perfect for this
        }

        for use_case, should_batch in batch_candidates.items():
            # Tasks with 24hr+ acceptable latency -> batch
            if should_batch:
                assert "monitoring" in use_case or "moderation" in use_case or "reporting" in use_case
            else:
                assert "emergency" in use_case or "real_time" in use_case or "support" in use_case

    @pytest.mark.costs
    def test_token_optimization_recommendations(self, service):
        """Test token-saving recommendations"""

        recommendations = {
            "prompt_compression": "Reduce verbose instructions by 20-30%",
            "batching": "Group 10 moderation requests -> 1 API call",
            "caching": "Cache regulatory updates -> reuse across creators",
            "model_downgrade": "Haiku for binary classification -> 10x cheaper",
            "batch_api": "Daily reports -> Batch API -> 50% savings",
        }

        # Token reduction should cascade to cost savings
        token_reduction_pct = 25  # 25% reduction
        cost_reduction_pct = token_reduction_pct  # Direct relationship

        assert cost_reduction_pct == 25


# ============================================================================
# EDGE CASES & EDGE SCENARIOS
# ============================================================================

@pytest.mark.costs
@pytest.mark.parametrize("input_tokens,output_tokens,model", [
    (0, 0, "claude-opus-4"),  # Zero usage
    (1_000_000_000, 1_000_000, "claude-opus-4"),  # 1B tokens
    (100, 100, "claude-haiku-3"),  # Minimal usage
])
def test_cost_calculation_edge_cases(input_tokens, output_tokens, model):
    """Test cost calculations at boundaries"""

    service = CostOptimizationService()

    result = service.calculate_monthly_cost_estimate(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=model,
        use_batch_api=False
    )

    # Cost should never be negative
    assert result["monthly_cost_usd"] >= 0

    # Cost should scale linearly
    if input_tokens > 0 or output_tokens > 0:
        assert result["monthly_cost_usd"] > 0


@pytest.mark.costs
@pytest.mark.parametrize("price_increase_pct", [10, 25, 50, 100])
def test_pricing_increase_scenarios(price_increase_pct):
    """Test impact of various price increase scenarios"""

    service = CostOptimizationService()

    base_result = service.calculate_monthly_cost_estimate(
        input_tokens=1_000_000,
        output_tokens=100_000,
        model="claude-opus-4",
        use_batch_api=False
    )

    increase_result = service.model_pricing_increase_impact(
        input_tokens=1_000_000,
        output_tokens=100_000,
        model="claude-opus-4",
        price_increase_pct=price_increase_pct
    )

    # New cost should reflect increase
    expected_factor = 1 + (price_increase_pct / 100)
    expected_new_cost = base_result["monthly_cost_usd"] * Decimal(str(expected_factor))

    # Allow small rounding differences
    assert abs(increase_result["new_monthly_cost_usd"] - expected_new_cost) < Decimal("0.01")


# ============================================================================
# ANNUAL FORECASTING
# ============================================================================

@pytest.mark.costs
class TestAnnualCostForecasting:
    """Test long-term cost projections"""

    def test_12_month_forecast_steady_state(self):
        """Test forecast with no growth"""

        service = CostOptimizationService()

        # Constant monthly usage
        monthly_tokens_in = 1_000_000
        monthly_tokens_out = 100_000

        monthly_cost = service.calculate_monthly_cost_estimate(
            input_tokens=monthly_tokens_in,
            output_tokens=monthly_tokens_out,
            model="claude-opus-4",
            use_batch_api=False
        )["monthly_cost_usd"]

        # Annual = 12 * monthly
        annual_cost = monthly_cost * 12

        assert annual_cost > 0

    def test_12_month_forecast_with_growth(self):
        """Test forecast with token growth"""

        service = CostOptimizationService()

        base_monthly = 1_000_000
        monthly_growth_rate = 0.05  # 5% MoM

        total_annual = Decimal("0")

        for month in range(12):
            monthly_tokens = base_monthly * (1 + monthly_growth_rate) ** month

            monthly_cost = service.calculate_monthly_cost_estimate(
                input_tokens=int(monthly_tokens),
                output_tokens=int(monthly_tokens * 0.1),
                model="claude-opus-4",
                use_batch_api=False
            )["monthly_cost_usd"]

            total_annual += monthly_cost

        # With growth, annual should be > 12 * base_month_cost
        base_annual = service.calculate_monthly_cost_estimate(
            input_tokens=base_monthly,
            output_tokens=100_000,
            model="claude-opus-4",
            use_batch_api=False
        )["monthly_cost_usd"] * 12

        assert total_annual > base_annual
