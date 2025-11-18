# Backtest Configuration UI - Complete Specification

**Date**: November 17, 2025  
**Purpose**: Complete specification for the Backtest Runner configuration UI with all parameters and tooltips

---

## 🎯 Overview

The Backtest Configuration UI should include **all trading parameters** that affect backtest results, organized into logical sections with helpful tooltips.

---

## 📋 Complete Configuration Form

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ Backtest Configuration                                    [Reset]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─ Date Range ───────────────────────────────────────────────────┐ │
│ │ Start Date *: [📅 Pick a date]                                │ │
│ │ End Date *:   [📅 Pick a date]                                │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ Stations ─────────────────────────────────────────────────────┐ │
│ │ Stations *:                                                     │ │
│ │   ☐ London (EGLC)                                              │ │
│ │   ☐ New York (KLGA)                                            │ │
│ │                                                                │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ Probability Model ────────────────────────────────────────────┐ │
│ │ Model Mode *:                                                   │ │
│ │   ● Spread Model  ○ Bands Model                                │ │
│ │                                                                 │ │
│ │ Zeus Likely %:    [0.80]  ⓘ 80% confidence level              │ │
│ │ Zeus Possible %:  [0.95]  ⓘ 95% confidence level              │ │
│ │ (Only used when Model Mode = "Bands Model")                    │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ Trading Parameters ───────────────────────────────────────────┐ │
│ │ Bankroll (USD) *:        [3000]  ⓘ Starting capital           │ │
│ │ Edge Minimum *:          [0.05]  ⓘ 0.05 = 5% minimum edge    │ │
│ │ Fee (bps) *:             [50]    ⓘ 50 bps = 0.5% fee         │ │
│ │ Slippage (bps) *:        [30]    ⓘ 30 bps = 0.3% slippage    │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ Risk Limits ──────────────────────────────────────────────────┐ │
│ │ Kelly Cap:              [0.10]  ⓘ Max 10% of bankroll per trade│ │
│ │ Per Market Cap (USD):   [500]   ⓘ Max position per bracket     │ │
│ │ Liquidity Min (USD):    [1000]  ⓘ Min market liquidity needed  │ │
│ └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ [Save Preset]                                    [Run Backtest]    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📝 Field Specifications

### Date Range Section

#### Start Date *
- **Type**: Date picker
- **Required**: Yes
- **Default**: None (user must select)
- **Format**: YYYY-MM-DD
- **Tooltip**: "First date to include in backtest. Must be before end date."
- **Validation**: Must be valid date, must be ≤ end date

#### End Date *
- **Type**: Date picker
- **Required**: Yes
- **Default**: None (user must select)
- **Format**: YYYY-MM-DD
- **Tooltip**: "Last date to include in backtest. Must be after start date."
- **Validation**: Must be valid date, must be ≥ start date

---

### Stations Section

#### Stations *
- **Type**: Multi-select checkboxes
- **Required**: Yes (at least one)
- **Default**: None (user must select)
- **Options**: 
  - London (EGLC)
  - New York (KLGA)
  - Chicago (KORD)
  - Los Angeles (KLAX)
  - [All stations from registry]
- **Tooltip**: "Select one or more weather stations to backtest. Each station will be evaluated independently."
- **Validation**: At least one station must be selected

---

### Probability Model Section

#### Model Mode *
- **Type**: Radio buttons
- **Required**: Yes
- **Default**: "spread"
- **Options**:
  - **Spread Model**: Uses hourly temperature spread × √2 to estimate uncertainty (default, Stage 3)
  - **Bands Model**: Uses Zeus's "likely" and "possible" confidence intervals (Stage 7B)
- **Tooltip**: 
  - **Spread Model**: "Estimates forecast uncertainty from the spread of hourly temperatures. More stable, works with all Zeus forecasts."
  - **Bands Model**: "Uses Zeus's confidence bands (likely/possible ranges) to estimate uncertainty. Requires Zeus to provide confidence data."
- **Validation**: Must be "spread" or "bands"

#### Zeus Likely %
- **Type**: Number input (0.0 to 1.0)
- **Required**: No (only when Model Mode = "bands")
- **Default**: 0.80
- **Step**: 0.01
- **Tooltip**: "Confidence level for Zeus 'likely' range. Default 80% (0.80). Only used with Bands Model."
- **Validation**: 0.0 ≤ value ≤ 1.0
- **Helper Text**: "0.80 = 80% confidence level"
- **Conditional**: Only visible/enabled when Model Mode = "bands"

#### Zeus Possible %
- **Type**: Number input (0.0 to 1.0)
- **Required**: No (only when Model Mode = "bands")
- **Default**: 0.95
- **Step**: 0.01
- **Tooltip**: "Confidence level for Zeus 'possible' range. Default 95% (0.95). Only used with Bands Model."
- **Validation**: 0.0 ≤ value ≤ 1.0, must be > Zeus Likely %
- **Helper Text**: "0.95 = 95% confidence level"
- **Conditional**: Only visible/enabled when Model Mode = "bands"

---

### Trading Parameters Section

#### Bankroll (USD) *
- **Type**: Number input
- **Required**: Yes
- **Default**: 3000
- **Min**: 100
- **Max**: 1000000
- **Step**: 100
- **Tooltip**: "Starting capital in USD for the backtest. This is the total amount available for trading."
- **Helper Text**: "Starting capital for simulation"

#### Edge Minimum *
- **Type**: Number input (0.0 to 1.0)
- **Required**: Yes
- **Default**: 0.05
- **Step**: 0.01
- **Tooltip**: "Minimum edge (advantage) required to place a trade. Edge = Zeus probability - Market probability - Fees - Slippage. Default 5% (0.05)."
- **Helper Text**: "0.05 = 5% minimum edge"
- **Validation**: 0.0 ≤ value ≤ 1.0

#### Fee (bps) *
- **Type**: Number input (basis points)
- **Required**: Yes
- **Default**: 50
- **Min**: 0
- **Max**: 1000
- **Step**: 1
- **Tooltip**: "Trading fees in basis points (1 bp = 0.01%). Includes Polymarket fees and any other transaction costs. Default 50 bps (0.5%)."
- **Helper Text**: "50 bps = 0.5% fee"
- **Validation**: 0 ≤ value ≤ 1000

#### Slippage (bps) *
- **Type**: Number input (basis points)
- **Required**: Yes
- **Default**: 30
- **Min**: 0
- **Max**: 500
- **Step**: 1
- **Tooltip**: "Expected slippage in basis points. Slippage is the difference between expected price and actual execution price. Default 30 bps (0.3%)."
- **Helper Text**: "30 bps = 0.3% slippage"
- **Validation**: 0 ≤ value ≤ 500

---

### Risk Limits Section

#### Kelly Cap
- **Type**: Number input (0.0 to 1.0)
- **Required**: No (uses default if not provided)
- **Default**: 0.10
- **Step**: 0.01
- **Tooltip**: "Maximum Kelly fraction per trade. Limits position size to prevent over-betting. Default 10% (0.10) means no single trade can exceed 10% of bankroll."
- **Helper Text**: "0.10 = 10% max of bankroll per trade"
- **Validation**: 0.0 < value ≤ 1.0

#### Per Market Cap (USD)
- **Type**: Number input
- **Required**: No (uses default if not provided)
- **Default**: 500
- **Min**: 10
- **Max**: 10000
- **Step**: 10
- **Tooltip**: "Maximum position size per market bracket in USD. Prevents over-concentration in a single bracket. Default $500."
- **Helper Text**: "Maximum position per bracket"
- **Validation**: 10 ≤ value ≤ 10000

#### Liquidity Min (USD)
- **Type**: Number input
- **Required**: No (uses default if not provided)
- **Default**: 1000
- **Min**: 100
- **Max**: 100000
- **Step**: 100
- **Tooltip**: "Minimum market liquidity required to place a trade. Markets with less liquidity are skipped to avoid large price impact. Default $1,000."
- **Helper Text**: "Minimum market liquidity needed"
- **Validation**: 100 ≤ value ≤ 100000

---

## 🎨 UI/UX Guidelines

### Tooltip Implementation

**Tooltip Icon**: Use an info icon (ⓘ) next to each field label

**Tooltip Behavior**:
- Hover: Show tooltip on hover
- Click: Toggle tooltip (for mobile)
- Position: Right side of field label, or below on mobile

**Tooltip Content**:
- Brief explanation (1-2 sentences)
- Default value if applicable
- When/why to change it
- Example values if helpful

### Helper Text

**Placement**: Below input field, smaller font, muted color

**Content**:
- Unit conversion (e.g., "50 bps = 0.5%")
- Default value reminder
- Format hint (e.g., "YYYY-MM-DD")

### Validation

**Real-time Validation**:
- Show errors immediately on blur
- Highlight invalid fields in red
- Show error message below field

**Submit Validation**:
- Disable "Run Backtest" button if form invalid
- Show summary of all errors
- Scroll to first error field

### Conditional Fields

**Model Mode Dependencies**:
- When "Spread Model" selected: Hide "Zeus Likely %" and "Zeus Possible %"
- When "Bands Model" selected: Show and enable "Zeus Likely %" and "Zeus Possible %"

**Visual Indication**:
- Fade out hidden fields
- Show transition animation
- Update form layout smoothly

---

## 📊 Default Values Reference

| Field | Default | Source |
|-------|---------|--------|
| Model Mode | "spread" | `config.model_mode` |
| Zeus Likely % | 0.80 | `config.zeus_likely_pct` |
| Zeus Possible % | 0.95 | `config.zeus_possible_pct` |
| Bankroll (USD) | 3000 | `config.trading.daily_bankroll_cap` |
| Edge Minimum | 0.05 | `config.trading.edge_min` |
| Fee (bps) | 50 | `config.trading.fee_bp` |
| Slippage (bps) | 30 | `config.trading.slippage_bp` |
| Kelly Cap | 0.10 | `config.trading.kelly_cap` |
| Per Market Cap (USD) | 500 | `config.trading.per_market_cap` |
| Liquidity Min (USD) | 1000 | `config.trading.liquidity_min_usd` |

---

## 🔌 API Request Format

### Current API (Needs Update)

```json
{
  "start_date": "2025-11-01",
  "end_date": "2025-11-13",
  "stations": ["EGLC", "KLGA"],
  "bankroll_usd": 3000,
  "edge_min": 0.05,
  "fee_bp": 50,
  "slippage_bp": 30
}
```

### Updated API (Recommended)

```json
{
  "start_date": "2025-11-01",
  "end_date": "2025-11-13",
  "stations": ["EGLC", "KLGA"],
  "model_mode": "spread",
  "zeus_likely_pct": 0.80,
  "zeus_possible_pct": 0.95,
  "bankroll_usd": 3000,
  "edge_min": 0.05,
  "fee_bp": 50,
  "slippage_bp": 30,
  "kelly_cap": 0.10,
  "per_market_cap": 500,
  "liquidity_min_usd": 1000
}
```

---

## ✅ Implementation Checklist

### Frontend
- [ ] Date range pickers (start/end date)
- [ ] Station multi-select checkboxes
- [ ] Model mode radio buttons (spread/bands)
- [ ] Conditional fields (Zeus Likely/Possible %)
- [ ] Trading parameters inputs (Bankroll, Edge, Fee, Slippage)
- [ ] Risk limits inputs (Kelly Cap, Per Market Cap, Liquidity Min)
- [ ] Tooltips for all fields
- [ ] Helper text for all fields
- [ ] Form validation
- [ ] Default values from config
- [ ] Save Preset functionality
- [ ] Load Preset functionality
- [ ] Reset button

### Backend
- [ ] Update `BacktestRequest` schema to include all parameters
- [ ] Update `BacktestService` to accept all parameters
- [ ] Update `Backtester` to use all parameters
- [ ] Pass parameters to `ProbabilityMapper` (model_mode, zeus_likely_pct, zeus_possible_pct)
- [ ] Pass parameters to `Sizer` (kelly_cap, per_market_cap, liquidity_min_usd)

---

## 📖 Tooltip Text Reference

### Quick Copy-Paste Tooltips

**Start Date**: "First date to include in backtest. Must be before end date."

**End Date**: "Last date to include in backtest. Must be after start date."

**Stations**: "Select one or more weather stations to backtest. Each station will be evaluated independently."

**Model Mode - Spread**: "Estimates forecast uncertainty from the spread of hourly temperatures. More stable, works with all Zeus forecasts."

**Model Mode - Bands**: "Uses Zeus's confidence bands (likely/possible ranges) to estimate uncertainty. Requires Zeus to provide confidence data."

**Zeus Likely %**: "Confidence level for Zeus 'likely' range. Default 80% (0.80). Only used with Bands Model."

**Zeus Possible %**: "Confidence level for Zeus 'possible' range. Default 95% (0.95). Only used with Bands Model."

**Bankroll (USD)**: "Starting capital in USD for the backtest. This is the total amount available for trading."

**Edge Minimum**: "Minimum edge (advantage) required to place a trade. Edge = Zeus probability - Market probability - Fees - Slippage. Default 5% (0.05)."

**Fee (bps)**: "Trading fees in basis points (1 bp = 0.01%). Includes Polymarket fees and any other transaction costs. Default 50 bps (0.5%)."

**Slippage (bps)**: "Expected slippage in basis points. Slippage is the difference between expected price and actual execution price. Default 30 bps (0.3%)."

**Kelly Cap**: "Maximum Kelly fraction per trade. Limits position size to prevent over-betting. Default 10% (0.10) means no single trade can exceed 10% of bankroll."

**Per Market Cap (USD)**: "Maximum position size per market bracket in USD. Prevents over-concentration in a single bracket. Default $500."

**Liquidity Min (USD)**: "Minimum market liquidity required to place a trade. Markets with less liquidity are skipped to avoid large price impact. Default $1,000."

---

**Last Updated**: November 17, 2025

