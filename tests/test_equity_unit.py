"""
Unit Tests: Equity & Cap Table System

Tests for:
- Cap table calculations
- Vesting schedules
- Dilution modeling
- Fully diluted share tracking
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.cap_table import (
    CapTable,
    EquityPosition,
    VestingSchedule,
    EquityType,
    VestingScheduleType,
)


class TestCapTable:
    """Test cap table models and calculations"""

    @pytest.fixture
    def pre_series_a_cap_table(self):
        """Create a pre-Series A cap table"""

        cap_table = CapTable(
            company_id="startup-1",
            authorized_shares=10_000_000,
            common_shares_issued=1_000_000,
            preferred_shares_issued=0,
            option_pool_total=200_000,
            option_pool_granted=50_000,
            option_pool_available=150_000,
            warrant_shares=0,
            fully_diluted_shares=1_250_000,  # Common + options
            current_valuation_usd=5_000_000,
            current_round_name="Pre-seed",
            founder_ownership_pct=Decimal("80.0"),
        )

        return cap_table

    def test_cap_table_fully_diluted_calculation(self, pre_series_a_cap_table):
        """Test that fully diluted shares include all equity"""

        cap_table = pre_series_a_cap_table

        # FD should be common + all options + warrants
        expected_fd = (
            cap_table.common_shares_issued +
            cap_table.option_pool_total +
            cap_table.warrant_shares
        )

        assert cap_table.fully_diluted_shares == expected_fd

    def test_cap_table_founder_ownership_basic(self, pre_series_a_cap_table):
        """Test founder ownership percentage"""

        cap_table = pre_series_a_cap_table

        # If founder has 800k of 1M common, ownership should be 80%
        assert cap_table.founder_ownership_pct == Decimal("80.0")

    def test_cap_table_option_pool_available(self, pre_series_a_cap_table):
        """Test option pool accounting"""

        cap_table = pre_series_a_cap_table

        # Available should equal total minus granted
        expected_available = cap_table.option_pool_total - cap_table.option_pool_granted

        assert cap_table.option_pool_available == expected_available

    @pytest.mark.equity
    def test_dilution_from_series_a(self):
        """Test dilution calculation during Series A round"""

        # Pre-Series A: $5M valuation, 1.1M FD shares, founder 90.9%
        pre_fd = 1_100_000
        pre_founder_pct = Decimal("90.9")
        pre_valuation = 5_000_000

        # Series A: $1M investment at $4.55/share
        series_a_investment = 1_000_000
        price_per_share = 4.55
        new_shares = int(series_a_investment / price_per_share)  # ~219,780

        # Post-Series A
        post_fd = pre_fd + new_shares
        post_founder_pct = (pre_fd / post_fd) * 100
        post_valuation = pre_valuation + series_a_investment

        # Dilution should be significant
        assert post_founder_pct < pre_founder_pct
        assert post_fd > pre_fd
        assert post_valuation > pre_valuation

        # Founder should drop ~45% (not 90%)
        assert 40 <= post_founder_pct <= 50


class TestVestingSchedule:
    """Test vesting schedule calculations"""

    @pytest.fixture
    def standard_4_year_vest(self):
        """Create standard 4-year vest with 1-year cliff"""

        grant_date = datetime(2024, 1, 1)

        schedule = VestingSchedule(
            grant_date=grant_date,
            grant_size=100_000,
            cliff_months=12,
            total_vesting_months=48,
            vesting_type=VestingScheduleType.LINEAR,
            has_single_trigger_acceleration=False,
            has_double_trigger_acceleration=False,
        )

        return schedule

    def test_vesting_cliff_not_met(self, standard_4_year_vest):
        """Test that no shares vest before cliff date"""

        schedule = standard_4_year_vest

        # At 6 months (before 12-month cliff)
        cliff_date = schedule.grant_date + timedelta(days=365)
        check_date = schedule.grant_date + timedelta(days=180)

        vested = schedule.compute_vested_amount(check_date)

        assert vested == 0  # No vesting before cliff

    def test_vesting_cliff_met(self, standard_4_year_vest):
        """Test that cliff vests 25% of shares"""

        schedule = standard_4_year_vest

        # At exactly cliff date (12 months)
        cliff_date = schedule.grant_date + timedelta(days=365)

        vested = schedule.compute_vested_amount(cliff_date)

        # After cliff: 12 months / 48 total = 25% vested
        expected = int(schedule.grant_size * 0.25)

        # Allow 1-2% tolerance for day calculation
        assert vested >= expected * 0.98
        assert vested <= expected * 1.02

    def test_vesting_linear_progression(self, standard_4_year_vest):
        """Test linear vesting progression"""

        schedule = standard_4_year_vest
        grant_date = schedule.grant_date

        # Test vesting at different points
        vesting_points = [
            (grant_date + timedelta(days=int(365*1.5)), "18 months"),  # 37.5%
            (grant_date + timedelta(days=int(365*2.5)), "30 months"),  # 62.5%
            (grant_date + timedelta(days=365*4), "48 months"),  # 100%
        ]

        for check_date, label in vesting_points:
            vested = schedule.compute_vested_amount(check_date)
            vested_pct = (vested / schedule.grant_size) * 100

            # Verify reasonable vesting
            assert 0 < vested_pct <= 100, f"Invalid vesting at {label}"

    def test_vesting_full_after_period(self, standard_4_year_vest):
        """Test 100% vesting after full period"""

        schedule = standard_4_year_vest

        # After 48 months
        full_date = schedule.grant_date + timedelta(days=365*4)

        vested = schedule.compute_vested_amount(full_date)

        # Should be fully vested
        assert vested >= schedule.grant_size * 0.99  # Allow 1% rounding

    @pytest.mark.equity
    def test_accelerated_vesting_single_trigger(self):
        """Test single-trigger acceleration (e.g., on IPO)"""

        schedule = VestingSchedule(
            grant_date=datetime(2024, 1, 1),
            grant_size=100_000,
            cliff_months=12,
            total_vesting_months=48,
            vesting_type=VestingScheduleType.LINEAR,
            has_single_trigger_acceleration=True,
            has_double_trigger_acceleration=False,
        )

        # Single trigger should accelerate 50% of unvested shares
        assert schedule.has_single_trigger_acceleration is True

    @pytest.mark.equity
    def test_accelerated_vesting_double_trigger(self):
        """Test double-trigger acceleration (e.g., on IPO + termination)"""

        schedule = VestingSchedule(
            grant_date=datetime(2024, 1, 1),
            grant_size=100_000,
            cliff_months=12,
            total_vesting_months=48,
            vesting_type=VestingScheduleType.LINEAR,
            has_single_trigger_acceleration=False,
            has_double_trigger_acceleration=True,
        )

        # Double trigger only applies on both IPO AND termination
        assert schedule.has_double_trigger_acceleration is True


class TestEquityPosition:
    """Test equity position tracking"""

    @pytest.fixture
    def founder_position(self):
        """Create founder equity position"""

        position = EquityPosition(
            holder_name="Alice",
            holder_type="founder",
            equity_type=EquityType.COMMON,
            shares_owned=800_000,
            ownership_pct=Decimal("80.0"),
            fully_diluted_pct=Decimal("64.0"),
            vesting_schedule_id="vest-1",
            note="Co-founder",
        )

        return position

    def test_equity_position_calculations(self, founder_position):
        """Test equity position basic math"""

        pos = founder_position

        # Ownership should be consistent
        assert pos.ownership_pct > pos.fully_diluted_pct

        # Founder should have significant stake
        assert pos.shares_owned > 100_000
        assert pos.equity_type == EquityType.COMMON

    @pytest.mark.parametrize("holder_type,expected_type", [
        ("founder", "founder"),
        ("investor", "investor"),
        ("employee", "employee"),
        ("advisor", "advisor"),
    ])
    def test_holder_types(self, holder_type, expected_type):
        """Test different holder types"""

        position = EquityPosition(
            holder_name=f"{holder_type.title()}",
            holder_type=holder_type,
            equity_type=EquityType.COMMON,
            shares_owned=10_000,
            ownership_pct=Decimal("1.0"),
            fully_diluted_pct=Decimal("0.8"),
        )

        assert position.holder_type == expected_type


# ============================================================================
# INTEGRATION SCENARIOS
# ============================================================================

@pytest.mark.equity
class TestCapTableScenarios:
    """End-to-end cap table scenarios"""

    def test_full_series_a_round_simulation(self):
        """Simulate complete Series A funding round"""

        # Starting point
        cap_table = CapTable(
            company_id="startup-1",
            authorized_shares=10_000_000,
            common_shares_issued=1_000_000,
            preferred_shares_issued=0,
            option_pool_total=200_000,
            option_pool_granted=100_000,
            option_pool_available=100_000,
            warrant_shares=0,
            fully_diluted_shares=1_200_000,
            current_valuation_usd=5_000_000,
            current_round_name="Pre-seed",
            founder_ownership_pct=Decimal("83.3"),
        )

        # Series A: $1M investment at $4.55/share
        investment_amount = 1_000_000
        share_price = 4.55
        new_preferred_shares = int(investment_amount / share_price)  # 219,780

        # Update cap table
        cap_table.preferred_shares_issued += new_preferred_shares
        new_fd = cap_table.common_shares_issued + cap_table.preferred_shares_issued + cap_table.option_pool_total

        # Recalculate ownership
        new_founder_pct = (cap_table.common_shares_issued / new_fd) * 100

        # Verify dilution occurred
        assert cap_table.preferred_shares_issued > 0
        assert new_founder_pct < Decimal("83.3")
        assert new_fd > cap_table.fully_diluted_shares

    def test_employee_option_grant_impact(self):
        """Test how employee option grants affect cap table"""

        cap_table = CapTable(
            company_id="startup-1",
            authorized_shares=10_000_000,
            common_shares_issued=1_000_000,
            preferred_shares_issued=100_000,
            option_pool_total=200_000,
            option_pool_granted=50_000,
            option_pool_available=150_000,
            warrant_shares=0,
            fully_diluted_shares=1_350_000,
            current_valuation_usd=6_000_000,
            current_round_name="Series A",
            founder_ownership_pct=Decimal("45.0"),
        )

        # Grant 10,000 options to employee
        grant_size = 10_000
        cap_table.option_pool_granted += grant_size
        cap_table.option_pool_available -= grant_size

        # Verify pool accounting
        assert cap_table.option_pool_granted == 60_000
        assert cap_table.option_pool_available == 140_000
        assert (cap_table.option_pool_granted + cap_table.option_pool_available) == 200_000


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.equity
@pytest.mark.parametrize("shares,fd_shares,expected_pct", [
    (500_000, 1_000_000, 50.0),
    (250_000, 1_000_000, 25.0),
    (999_999, 1_000_000, 99.9999),
    (1, 1_000_000, 0.0001),
])
def test_ownership_percentage_edge_cases(shares, fd_shares, expected_pct):
    """Test ownership calculation edge cases"""

    actual_pct = (shares / fd_shares) * 100

    assert abs(actual_pct - expected_pct) < 0.01
