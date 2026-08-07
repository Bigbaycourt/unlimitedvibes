"""
Cost Optimization Service

Handles:
- Anthropic API cost calculations
- Batch API savings modeling
- Competitor pricing comparison
- Price increase impact modeling
- Annual budget forecasting
- Per-feature cost estimation
"""

from decimal import Decimal
from typing import Any, Dict, List


class CostOptimizationService:
    """Service for calculating and optimizing AI API costs."""

    # Current pricing as of 2026 (post-50% increase)
    CURRENT_PRICING: Dict[str, Dict[str, Decimal]] = {
        "claude-opus-4": {
            "input_cost_per_mtok": Decimal("4.50"),
            "output_cost_per_mtok": Decimal("22.50"),
        },
        "claude-sonnet-4": {
            "input_cost_per_mtok": Decimal("0.80"),
            "output_cost_per_mtok": Decimal("4.00"),
        },
        "claude-haiku-3": {
            "input_cost_per_mtok": Decimal("0.25"),
            "output_cost_per_mtok": Decimal("1.25"),
        },
    }

    # Competitor pricing (approximate)
    COMPETITOR_PRICING: Dict[str, Dict[str, Decimal]] = {
        "openai": {
            "input_cost_per_mtok": Decimal("2.50"),
            "output_cost_per_mtok": Decimal("10.00"),
        },
        "google": {
            "input_cost_per_mtok": Decimal("1.25"),
            "output_cost_per_mtok": Decimal("5.00"),
        },
    }

    # Estimated monthly token usage per feature
    FEATURE_ESTIMATES: Dict[str, Dict[str, Any]] = {
        "content_moderation": {
            "model": "claude-haiku-3",
            "input_tokens": 500_000,
            "output_tokens": 50_000,
        },
        "content_generation": {
            "model": "claude-opus-4",
            "input_tokens": 2_000_000,
            "output_tokens": 500_000,
        },
        "compliance_monitoring": {
            "model": "claude-sonnet-4",
            "input_tokens": 1_000_000,
            "output_tokens": 100_000,
        },
        "creator_support": {
            "model": "claude-sonnet-4",
            "input_tokens": 500_000,
            "output_tokens": 200_000,
        },
    }

    BATCH_API_DISCOUNT = Decimal("0.5")  # 50% off

    def calculate_monthly_cost_estimate(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        use_batch_api: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculate estimated monthly cost for given token usage.

        Args:
            input_tokens: Monthly input token count
            output_tokens: Monthly output token count
            model: Model identifier (e.g., "claude-opus-4")
            use_batch_api: Whether to apply Batch API 50% discount

        Returns:
            dict with monthly_cost_usd, model, breakdown
        """
        pricing = self.CURRENT_PRICING[model]

        input_cost = (
            Decimal(str(input_tokens)) / Decimal("1000000")
        ) * pricing["input_cost_per_mtok"]

        output_cost = (
            Decimal(str(output_tokens)) / Decimal("1000000")
        ) * pricing["output_cost_per_mtok"]

        total = input_cost + output_cost

        if use_batch_api:
            total = total * self.BATCH_API_DISCOUNT

        return {
            "monthly_cost_usd": total,
            "model": model,
            "input_cost_usd": input_cost * (self.BATCH_API_DISCOUNT if use_batch_api else Decimal("1")),
            "output_cost_usd": output_cost * (self.BATCH_API_DISCOUNT if use_batch_api else Decimal("1")),
            "batch_api": use_batch_api,
        }

    def get_cost_per_feature(
        self, features: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Estimate monthly cost for each feature/service.

        Args:
            features: List of feature names to estimate

        Returns:
            dict mapping feature name to cost estimate
        """
        result = {}

        for feature in features:
            if feature in self.FEATURE_ESTIMATES:
                est = self.FEATURE_ESTIMATES[feature]
                cost = self.calculate_monthly_cost_estimate(
                    input_tokens=est["input_tokens"],
                    output_tokens=est["output_tokens"],
                    model=est["model"],
                    use_batch_api=False,
                )
                result[feature] = {
                    "monthly_cost_usd": cost["monthly_cost_usd"],
                    "model": est["model"],
                    "input_tokens": est["input_tokens"],
                    "output_tokens": est["output_tokens"],
                }
            else:
                result[feature] = {
                    "monthly_cost_usd": Decimal("0"),
                    "model": "unknown",
                    "input_tokens": 0,
                    "output_tokens": 0,
                }

        return result

    def compare_to_competitors(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare Anthropic costs to competitor pricing.

        Args:
            input_tokens: Token count for comparison
            output_tokens: Token count for comparison

        Returns:
            dict with provider costs
        """
        input_millions = Decimal(str(input_tokens)) / Decimal("1000000")
        output_millions = Decimal(str(output_tokens)) / Decimal("1000000")

        # Anthropic (using Sonnet as default comparison model)
        anthropic_pricing = self.CURRENT_PRICING["claude-sonnet-4"]
        anthropic_cost = (
            input_millions * anthropic_pricing["input_cost_per_mtok"]
            + output_millions * anthropic_pricing["output_cost_per_mtok"]
        )

        result = {
            "anthropic": {"estimated_cost_usd": anthropic_cost},
        }

        for provider, pricing in self.COMPETITOR_PRICING.items():
            cost = (
                input_millions * pricing["input_cost_per_mtok"]
                + output_millions * pricing["output_cost_per_mtok"]
            )
            result[provider] = {"estimated_cost_usd": cost}

        return result

    def model_pricing_increase_impact(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        price_increase_pct: int,
    ) -> Dict[str, Any]:
        """
        Model the financial impact of a price increase.

        Args:
            input_tokens: Monthly input tokens
            output_tokens: Monthly output tokens
            model: Model identifier
            price_increase_pct: Percentage increase (e.g., 20 for 20%)

        Returns:
            dict with new_monthly_cost_usd, cost_increase_usd, increase_pct
        """
        current = self.calculate_monthly_cost_estimate(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            use_batch_api=False,
        )

        increase_factor = Decimal("1") + Decimal(str(price_increase_pct)) / Decimal("100")
        new_cost = current["monthly_cost_usd"] * increase_factor
        cost_increase = new_cost - current["monthly_cost_usd"]

        return {
            "current_monthly_cost_usd": current["monthly_cost_usd"],
            "new_monthly_cost_usd": new_cost,
            "cost_increase_usd": cost_increase,
            "increase_pct": price_increase_pct,
            "model": model,
        }
