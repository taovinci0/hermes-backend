# Changelog

All notable changes to the Hermes project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Stage 4: Polymarket adapters (discovery + pricing)
- Stage 5: Edge calculation & Kelly sizing
- Stage 6: Paper execution loop (MVP)
- Stage 7: Backtest harness

## [1.0.0] - 2025-11-04

### Stage 3: Probability Mapper ✅

#### Added
- **Probability Mapper Implementation**
  - `agents/prob_mapper.py` - Normal CDF-based probability computation
  - Daily high μ calculation (max of hourly temps)
  - Empirical sigma estimation from forecast spread
  - Probability normalization (sum = 1.0)
  - Sigma clamping guardrails (σ ∈ [0.5, 10.0]°F)
  
- **Comprehensive Test Suite**
  - `tests/test_prob_mapper.py` - 14 tests for probability mapping
  - Tests for normalization, monotonicity, sigma impact
  - Edge case handling (empty data, extreme temps)
  - CDF computation validation
  
- **Dependencies**
  - Added `scipy>=1.11.0` for normal CDF calculations
  - Updated `pyproject.toml` and `requirements.txt`

#### Changed
- `core/orchestrator.py` - Implemented `run_probmap()` command
  - Full Zeus → probability pipeline
  - Automatic bracket generation around forecast range
  - Top-5 bracket display

#### Test Coverage
- 60 tests total (35 Stage 1 + 11 Stage 2 + 14 Stage 3)
- 100% pass rate (60/60)
- Test execution time: 13.62s

### Stage 2: Zeus Forecast Agent ✅

(See previous changelog entry below)

## [1.0.0] - 2025-11-04

### Stage 1: Data Registry + Utilities ✅

#### Added
- **Station Registry System**
  - `core/registry.py` - Station metadata loader with lookup methods
  - `data/registry/stations.csv` - 16 global weather stations
  - Station lookup by code, city name, timezone
  - Singleton pattern for global registry access
  
- **Comprehensive Time Utility Tests**
  - `tests/test_time_utils.py` - 14 tests for DST edge cases
  - Spring/fall DST transition testing
  - Cross-timezone conversion validation
  - Date boundary handling tests
  
- **Station Registry Tests**
  - `tests/test_registry.py` - 13 tests for registry operations
  - CSV loading and parsing tests
  - Coordinate and timezone validation
  - Lookup and filtering tests
  
- **Verification**
  - `verify_stage1.py` - Automated Stage 1 verification script
  - Integration testing for registry + time utils
  
- **Documentation**
  - `STAGE_1_COMPLETE.md` - Complete Stage 1 documentation
  - `CHANGELOG.md` - This file

#### Changed
- `core/__init__.py` - Added registry module to exports

#### Test Coverage
- 35 tests total (8 units + 14 time + 13 registry)
- 100% pass rate (35/35)
- Test execution time: 0.31s

### Stage 0: Repository Bootstrap ✅

#### Added
- **Core Infrastructure**
  - `core/orchestrator.py` - Main CLI with all modes (fetch, probmap, paper, backtest)
  - `core/config.py` - Configuration management (env vars + YAML)
  - `core/types.py` - Pydantic models for all data structures
  - `core/units.py` - Temperature conversion utilities (K↔C↔F)
  - `core/time_utils.py` - DST-aware timezone helpers
  - `core/logger.py` - Structured logging with rich formatting

- **Agent Stubs**
  - `agents/zeus_forecast.py` - Zeus API client (Stage 2 stub)
  - `agents/prob_mapper.py` - Probability mapper (Stage 3 stub)
  - `agents/edge_and_sizing.py` - Kelly sizer (Stage 5 stub)

- **Venue Adapters**
  - `venues/polymarket/discovery.py` - Market discovery (Stage 4 stub)
  - `venues/polymarket/pricing.py` - Price reading (Stage 4 stub)
  - `venues/polymarket/execute.py` - Paper/live brokers (Stage 6/8 stubs)
  - `venues/polymarket/schemas.py` - API DTOs

- **Data Structure**
  - `data/registry/` - Station metadata directory
  - `data/snapshots/` - API pull storage
  - `data/trades/` - Trade logs
  - `data/runs/` - Backtest results

- **Tests**
  - `tests/test_units.py` - 8 temperature conversion tests
  - Test framework configured with pytest

- **Development Tools**
  - `pyproject.toml` - Modern Python packaging
  - `requirements.txt` - Alternative pip install
  - `Makefile` - Common development tasks
  - `.gitignore` - Git excludes
  - `.env.example` - Configuration template

- **Documentation**
  - `README.md` - Quick start guide
  - `PROJECT_OVERVIEW.md` - Complete 11-stage implementation plan
  - `STAGE_0_COMPLETE.md` - Stage 0 deliverables
  - `STAGE_0_VERIFICATION.md` - Detailed verification results
  - `QUICK_REFERENCE.md` - Command cheat sheet
  - `LICENSE` - MIT License

- **Verification**
  - `verify_stage0.py` - Automated Stage 0 verification

#### Test Coverage
- 8 tests for unit conversions
- 100% pass rate
- Test execution time: 0.06s

---

## Version History

- **1.0.0** (2025-11-04) - Stage 0 + Stage 1 complete
- Repository initialized with complete scaffold and data registry

---

**Next Release**: Stage 2 (Zeus Forecast Agent)

