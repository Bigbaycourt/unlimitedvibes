# Testing Guide: Unlimited Vibes Backend

Complete testing setup for compliance, equity, and cost optimization systems.

---

## Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_compliance_unit.py

# Run by marker
pytest -m compliance    # Compliance tests only
pytest -m equity        # Equity tests only
pytest -m costs         # Cost tests only
pytest -m unit          # Fast unit tests
pytest -m integration   # Integration tests
```

---

## Test Structure

### Test Files

| File | Purpose | Tests |
|------|---------|-------|
| `test_compliance_unit.py` | Content moderation, scoring, regulatory | 20+ unit tests |
| `test_equity_unit.py` | Cap table, vesting, dilution | 18+ unit tests |
| `test_costs_unit.py` | Cost calculation, forecasting, optimization | 15+ unit tests |
| `test_integration_api.py` | End-to-end API workflows | 15+ integration tests |
| `conftest.py` | Shared fixtures and configuration | - |

### Test Markers

```bash
# Run tests by marker
pytest -m compliance        # Compliance system tests
pytest -m equity            # Equity system tests
pytest -m costs             # Cost optimization tests
pytest -m integration       # Integration tests (require DB)
pytest -m unit              # Fast unit tests (no DB)
pytest -m slow              # Slow tests (network, external APIs)

# Combine markers
pytest -m "not slow"        # Everything except slow tests
pytest -m "unit and costs"  # Unit tests that test costs
```

---

## Running Tests with Coverage

```bash
# Run tests with coverage report
pytest --cov=app --cov-report=html

# Generate coverage report
coverage report

# View HTML report
open htmlcov/index.html

# Coverage by module
pytest --cov=app.services --cov=app.models --cov-report=term-missing
```

---

## Parallel Test Execution

```bash
# Run tests in parallel (4 workers)
pytest -n 4

# Distribute by test file
pytest -n auto
```

---

## Debugging Tests

```bash
# Run with pdb on failure
pytest --pdb

# Stop after first failure
pytest -x

# Show print statements
pytest -s

# Verbose + show local variables
pytest -vv -l

# Specific test with debugging
pytest tests/test_compliance_unit.py::TestContentModerationService::test_moderate_content_safe -vv -s
```

---

## Continuous Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run tests
        run: pytest -v --cov=app

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### "Event loop is closed" Error

```python
@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### Database Connection Errors

```bash
# Use in-memory SQLite for tests
DATABASE_URL="sqlite+aiosqlite:///:memory:"
pytest
```

### Async Timeout

```bash
# Run with timeout (60s per test)
pytest --timeout=60
```

### Import Errors

```bash
# Make sure backend directory is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/unlimited-vibes/backend"
pytest
```

---

## Test Coverage Goals

| System | Target | Current |
|--------|--------|---------|
| Compliance | 90% | TBD |
| Equity | 85% | TBD |
| Costs | 90% | TBD |
| API Routes | 80% | TBD |

---

**Last Updated**: 2026-08-07
**Test Count**: 68 tests (unit + integration)
**Async Support**: Full pytest-asyncio integration
