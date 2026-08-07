"""
Cap Table Models

Models for:
- Cap table structure and calculations
- Equity positions (founders, investors, employees)
- Vesting schedules with cliff and acceleration
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional


class EquityType(str, Enum):
    COMMON = "common"
    PREFERRED = "preferred"
    OPTIONS = "options"
    WARRANTS = "warrants"
    RSU = "rsu"


class VestingScheduleType(str, Enum):
    LINEAR = "linear"
    BACK_LOADED = "back_loaded"
    FRONT_LOADED = "front_loaded"
    CUSTOM = "custom"


class CapTable:
    """Cap table with fully diluted share calculations"""

    def __init__(
        self,
        company_id: str,
        authorized_shares: int,
        common_shares_issued: int,
        preferred_shares_issued: int,
        option_pool_total: int,
        option_pool_granted: int,
        option_pool_available: int,
        warrant_shares: int,
        current_valuation_usd: int,
        current_round_name: str,
        founder_ownership_pct: Decimal,
        fully_diluted_shares: int = 0,  # Accepted but computed via property
    ):
        self.company_id = company_id
        self.authorized_shares = authorized_shares
        self.common_shares_issued = common_shares_issued
        self.preferred_shares_issued = preferred_shares_issued
        self.option_pool_total = option_pool_total
        self.option_pool_granted = option_pool_granted
        self.option_pool_available = option_pool_available
        self.warrant_shares = warrant_shares
        self.current_valuation_usd = current_valuation_usd
        self.current_round_name = current_round_name
        self.founder_ownership_pct = founder_ownership_pct

    @property
    def fully_diluted_shares(self) -> int:
        """Compute fully diluted shares: common + preferred + full option pool + warrants"""
        return (
            self.common_shares_issued
            + self.preferred_shares_issued
            + self.option_pool_total
            + self.warrant_shares
        )

    @fully_diluted_shares.setter
    def fully_diluted_shares(self, value: int):
        # Accept the value for construction but don't store it;
        # the property always computes from components.
        pass


@dataclass
class EquityPosition:
    """A single holder's equity position"""

    holder_name: str
    holder_type: str  # founder, investor, employee, advisor
    equity_type: EquityType
    shares_owned: int
    ownership_pct: Decimal
    fully_diluted_pct: Decimal
    vesting_schedule_id: Optional[str] = None
    note: Optional[str] = None


@dataclass
class VestingSchedule:
    """Vesting schedule with cliff, linear vesting, and acceleration"""

    grant_date: datetime
    grant_size: int
    cliff_months: int
    total_vesting_months: int
    vesting_type: VestingScheduleType
    has_single_trigger_acceleration: bool = False
    has_double_trigger_acceleration: bool = False

    def compute_vested_amount(self, check_date: datetime) -> int:
        """
        Calculate vested shares at a given date.

        Returns 0 before cliff, then linear vesting to 100% at end of period.
        """
        if check_date <= self.grant_date:
            return 0

        # Calculate months elapsed (using average days per month)
        days_elapsed = (check_date - self.grant_date).days
        months_elapsed = days_elapsed / 30.4375  # Average days per month

        # Before cliff: nothing vests
        if months_elapsed < self.cliff_months:
            return 0

        # After full period: everything vested
        if months_elapsed >= self.total_vesting_months:
            return self.grant_size

        # Linear vesting
        vested_fraction = months_elapsed / self.total_vesting_months
        return int(self.grant_size * vested_fraction)
