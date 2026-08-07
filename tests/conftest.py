"""
Shared pytest fixtures and configuration

Fixtures for:
- Async client setup
- Database fixtures
- Mock services
- Test data
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ============================================================================
# ASYNC HTTP CLIENT
# ============================================================================

@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client for testing endpoints"""

    async with AsyncClient(base_url="http://testserver") as client:
        yield client


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def db_url():
    """Test database URL"""
    # Use SQLite in-memory for fast tests
    return "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_engine(db_url):
    """Async SQLAlchemy engine for tests"""

    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session_maker(async_engine):
    """Session factory for tests"""

    async_session = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return async_session


@pytest_asyncio.fixture
async def db_session(async_engine, async_session_maker):
    """Database session for individual tests"""

    # Create tables
    from app.models import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Yield session
    async with async_session_maker() as session:
        yield session


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def test_creator_data():
    """Sample creator data for testing"""

    return {
        "creator_id": "creator-123",
        "name": "Test Creator",
        "email": "creator@example.com",
        "primary_platform": "instagram",
        "follower_count": 100_000,
        "bio": "Content creator and influencer",
    }


@pytest.fixture
def test_compliance_record():
    """Sample compliance record"""

    from app.services.compliance_scoring import PostComplianceRecord

    return PostComplianceRecord(
        post_id="post-1",
        platform="instagram",
        posted_at=datetime.utcnow(),
        is_sponsored=True,
        has_disclosure_tag=True,
        was_flagged_by_platform=False,
        ai_generated=False,
        ai_disclosure_present=False,
    )


@pytest.fixture
def test_cap_table_data():
    """Sample cap table for testing"""

    from decimal import Decimal

    return {
        "company_id": "startup-1",
        "authorized_shares": 10_000_000,
        "common_shares_issued": 1_000_000,
        "preferred_shares_issued": 0,
        "option_pool_total": 200_000,
        "option_pool_granted": 50_000,
        "option_pool_available": 150_000,
        "warrant_shares": 0,
        "fully_diluted_shares": 1_250_000,
        "current_valuation_usd": 5_000_000,
        "current_round_name": "Pre-seed",
        "founder_ownership_pct": Decimal("80.0"),
    }


@pytest.fixture
def test_vesting_schedule():
    """Sample vesting schedule"""

    from app.models.cap_table import VestingScheduleType

    return {
        "grant_date": datetime(2024, 1, 1),
        "grant_size": 100_000,
        "cliff_months": 12,
        "total_vesting_months": 48,
        "vesting_type": VestingScheduleType.LINEAR,
        "has_single_trigger_acceleration": False,
        "has_double_trigger_acceleration": False,
    }


# ============================================================================
# MOCK SERVICE FIXTURES
# ============================================================================

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client"""

    from unittest.mock import AsyncMock

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        return_value={
            "content": [{"text": "Mock response"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }
    )

    return mock_client


@pytest.fixture
def mock_stripe_client():
    """Mock Stripe client"""

    from unittest.mock import AsyncMock

    mock_client = AsyncMock()
    mock_client.Account.retrieve = AsyncMock(
        return_value={"id": "acct_test123"}
    )

    return mock_client


# ============================================================================
# MARKER-BASED SETUP
# ============================================================================

def pytest_configure(config):
    """Register custom markers"""

    config.addinivalue_line(
        "markers", "compliance: Test compliance & moderation"
    )
    config.addinivalue_line(
        "markers", "equity: Test equity & cap table"
    )
    config.addinivalue_line(
        "markers", "costs: Test cost optimization"
    )
    config.addinivalue_line(
        "markers", "integration: Test integration with DB"
    )
    config.addinivalue_line(
        "markers", "slow: Test requires external API calls"
    )
    config.addinivalue_line(
        "markers", "unit: Fast unit tests"
    )


# ============================================================================
# ASYNC SETUP
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

@pytest.fixture(autouse=True)
def set_test_env_vars(monkeypatch):
    """Set environment variables for tests"""

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DEBUG", "true")
