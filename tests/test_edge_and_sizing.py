"""Tests for edge calculation and Kelly sizing.

Stage 5 implementation.
"""

import pytest
from datetime import datetime, timezone

from agents.edge_and_sizing import Sizer
from core.types import BracketProb, MarketBracket
from venues.polymarket.schemas import MarketDepth


def test_sizer_initialization() -> None:
    """Test Sizer initialization with config values."""
    sizer = Sizer(
        edge_min=0.05,
        fee_bp=50,
        slippage_bp=30,
        kelly_cap=0.10,
        per_market_cap=500.0,
        liquidity_min_usd=1000.0,
    )
    
    assert sizer.edge_min == 0.05
    assert sizer.fee_bp == 50
    assert sizer.slippage_bp == 30
    assert sizer.kelly_cap == 0.10
    assert sizer.per_market_cap == 500.0
    assert sizer.liquidity_min_usd == 1000.0


def test_edge_calculation() -> None:
    """Test edge = (p_zeus - p_mkt) - fees - slippage."""
    sizer = Sizer(edge_min=0.05, fee_bp=50, slippage_bp=30)
    
    # p_zeus=0.60, p_mkt=0.50, fees=0.0050, slip=0.0030
    # edge = 0.10 - 0.0050 - 0.0030 = 0.0920
    edge = sizer.compute_edge(p_zeus=0.60, p_mkt=0.50)
    
    assert edge == pytest.approx(0.0920, abs=1e-6)


def test_edge_calculation_negative() -> None:
    """Test edge calculation with negative edge."""
    sizer = Sizer(edge_min=0.05, fee_bp=50, slippage_bp=30)
    
    # p_zeus=0.50, p_mkt=0.55 → negative edge before costs
    edge = sizer.compute_edge(p_zeus=0.50, p_mkt=0.55)
    
    # -0.05 - 0.0050 - 0.0030 = -0.0580
    assert edge == pytest.approx(-0.0580, abs=1e-6)
    assert edge < 0


def test_kelly_fraction_basic() -> None:
    """Test Kelly fraction calculation for binary outcomes."""
    sizer = Sizer()
    
    # For price=0.50 (b=1), p_zeus=0.60:
    # f* = (1*0.60 - 0.40)/1 = 0.20
    f_kelly = sizer.compute_kelly_fraction(p_zeus=0.60, price=0.50)
    
    assert f_kelly == pytest.approx(0.20, abs=1e-6)


def test_kelly_fraction_different_price() -> None:
    """Test Kelly fraction with non-50% price."""
    sizer = Sizer()
    
    # For price=0.40 (b=1.5), p_zeus=0.70:
    # f* = (1.5*0.70 - 0.30)/1.5 = (1.05 - 0.30)/1.5 = 0.50
    f_kelly = sizer.compute_kelly_fraction(p_zeus=0.70, price=0.40)
    
    assert f_kelly == pytest.approx(0.50, abs=1e-6)


def test_kelly_fraction_negative_edge() -> None:
    """Test Kelly fraction returns 0 for negative edge."""
    sizer = Sizer()
    
    # p_zeus=0.40, price=0.50 → negative edge
    f_kelly = sizer.compute_kelly_fraction(p_zeus=0.40, price=0.50)
    
    # Should return 0 (don't bet on negative edge)
    assert f_kelly == 0.0


def test_kelly_fraction_invalid_price() -> None:
    """Test Kelly fraction with invalid prices."""
    sizer = Sizer()
    
    # Price <= 0
    assert sizer.compute_kelly_fraction(p_zeus=0.60, price=0.0) == 0.0
    assert sizer.compute_kelly_fraction(p_zeus=0.60, price=-0.1) == 0.0
    
    # Price >= 1
    assert sizer.compute_kelly_fraction(p_zeus=0.60, price=1.0) == 0.0
    assert sizer.compute_kelly_fraction(p_zeus=0.60, price=1.5) == 0.0


def test_decide_basic() -> None:
    """Test basic decision generation with positive edge."""
    sizer = Sizer(
        edge_min=0.05,
        fee_bp=50,
        slippage_bp=30,
        kelly_cap=0.10,
        per_market_cap=500.0,
    )
    
    # Create bracket with positive edge
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    prob = BracketProb(
        bracket=bracket,
        p_zeus=0.65,  # Zeus thinks 65%
        p_mkt=0.50,   # Market thinks 50%
        sigma_z=2.0,
    )
    
    decisions = sizer.decide([prob], bankroll_usd=1000.0)
    
    assert len(decisions) == 1
    
    decision = decisions[0]
    assert decision.bracket.name == "59-60°F"
    
    # Edge = 0.65 - 0.50 - 0.0050 - 0.0030 = 0.1420
    assert decision.edge == pytest.approx(0.1420, abs=1e-4)
    
    # Kelly: b = 1/0.50 - 1 = 1.0, f* = (1*0.65 - 0.35)/1 = 0.30
    assert decision.f_kelly == pytest.approx(0.30, abs=1e-4)
    
    # Size = min(f_kelly * bankroll, kelly_cap * bankroll, per_market_cap)
    # = min(300, 100, 500) = 100
    assert decision.size_usd == pytest.approx(100.0, abs=0.01)


def test_decide_filters_low_edge() -> None:
    """Test that brackets with edge < edge_min are filtered out."""
    sizer = Sizer(edge_min=0.05, fee_bp=50, slippage_bp=30)
    
    # Create bracket with low edge
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    prob = BracketProb(
        bracket=bracket,
        p_zeus=0.51,  # Only 1% raw edge
        p_mkt=0.50,
        sigma_z=2.0,
    )
    
    decisions = sizer.decide([prob], bankroll_usd=1000.0)
    
    # Edge = 0.01 - 0.0050 - 0.0030 = 0.0020 < 0.05
    assert len(decisions) == 0


def test_decide_per_market_cap() -> None:
    """Test that position size never exceeds per_market_cap."""
    sizer = Sizer(
        edge_min=0.01,
        fee_bp=10,
        slippage_bp=10,
        kelly_cap=0.50,     # High cap
        per_market_cap=250.0,  # Low per-market cap
    )
    
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    prob = BracketProb(
        bracket=bracket,
        p_zeus=0.80,  # Strong edge
        p_mkt=0.50,
        sigma_z=2.0,
    )
    
    decisions = sizer.decide([prob], bankroll_usd=10000.0)
    
    assert len(decisions) == 1
    # Even if Kelly suggests more, should cap at $250
    assert decisions[0].size_usd <= 250.0


def test_decide_kelly_cap() -> None:
    """Test that Kelly fraction is capped."""
    sizer = Sizer(
        edge_min=0.01,
        fee_bp=10,
        slippage_bp=10,
        kelly_cap=0.05,  # 5% max
        per_market_cap=1000.0,
    )
    
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    prob = BracketProb(
        bracket=bracket,
        p_zeus=0.80,  # Would suggest high Kelly
        p_mkt=0.40,
        sigma_z=2.0,
    )
    
    decisions = sizer.decide([prob], bankroll_usd=1000.0)
    
    assert len(decisions) == 1
    # Should be capped at 5% of $1000 = $50
    assert decisions[0].size_usd == pytest.approx(50.0, abs=0.01)


def test_decide_liquidity_filter() -> None:
    """Test that illiquid markets are skipped."""
    sizer = Sizer(
        edge_min=0.01,
        fee_bp=10,
        slippage_bp=10,
        liquidity_min_usd=1000.0,  # Require $1000 min
    )
    
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    prob = BracketProb(
        bracket=bracket,
        p_zeus=0.65,
        p_mkt=0.50,
        sigma_z=2.0,
    )
    
    # Provide low liquidity
    depth_data = {
        "m1": MarketDepth(
            token_id="m1",
            bid_depth_usd=500.0,  # Below minimum
            ask_depth_usd=500.0,
        )
    }
    
    decisions = sizer.decide([prob], bankroll_usd=10000.0, depth_data=depth_data)
    
    # Should be filtered out due to low liquidity
    assert len(decisions) == 0


def test_decide_liquidity_cap() -> None:
    """Test that position size is capped by available liquidity."""
    sizer = Sizer(
        edge_min=0.01,
        fee_bp=10,
        slippage_bp=10,
        kelly_cap=0.50,
        per_market_cap=5000.0,
        liquidity_min_usd=1000.0,
    )
    
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    prob = BracketProb(
        bracket=bracket,
        p_zeus=0.70,
        p_mkt=0.50,
        sigma_z=2.0,
    )
    
    # Provide limited liquidity
    depth_data = {
        "m1": MarketDepth(
            token_id="m1",
            bid_depth_usd=1500.0,  # Limited liquidity
            ask_depth_usd=2000.0,
        )
    }
    
    decisions = sizer.decide([prob], bankroll_usd=10000.0, depth_data=depth_data)
    
    assert len(decisions) == 1
    # Should be capped at available liquidity
    assert decisions[0].size_usd <= 1500.0


def test_decide_multiple_brackets() -> None:
    """Test decision generation for multiple brackets."""
    sizer = Sizer(edge_min=0.05, fee_bp=50, slippage_bp=30)
    
    brackets_data = [
        ("59-60°F", 59, 60, "m1", 0.20, 0.10),  # Strong edge
        ("60-61°F", 60, 61, "m2", 0.62, 0.50),  # Good edge
        ("61-62°F", 61, 62, "m3", 0.52, 0.50),  # Weak edge (filtered)
        ("62-63°F", 62, 63, "m4", 0.45, 0.50),  # Negative (filtered)
    ]
    
    probs = []
    for name, lower, upper, mid, p_z, p_m in brackets_data:
        bracket = MarketBracket(name=name, lower_F=lower, upper_F=upper, market_id=mid)
        prob = BracketProb(bracket=bracket, p_zeus=p_z, p_mkt=p_m, sigma_z=2.0)
        probs.append(prob)
    
    decisions = sizer.decide(probs, bankroll_usd=5000.0)
    
    # Should have 2 decisions (first two have enough edge)
    assert len(decisions) == 2
    assert decisions[0].bracket.name == "59-60°F"
    assert decisions[1].bracket.name == "60-61°F"


def test_decide_empty_probs() -> None:
    """Test decide with empty probabilities list."""
    sizer = Sizer()
    
    with pytest.raises(ValueError, match="No bracket probabilities"):
        sizer.decide([], bankroll_usd=1000.0)


def test_decide_missing_p_mkt() -> None:
    """Test decide skips brackets without market probability."""
    sizer = Sizer(edge_min=0.01)
    
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    prob = BracketProb(
        bracket=bracket,
        p_zeus=0.65,
        p_mkt=None,  # Missing market probability
        sigma_z=2.0,
    )
    
    decisions = sizer.decide([prob], bankroll_usd=1000.0)
    
    # Should skip due to missing p_mkt
    assert len(decisions) == 0


def test_decide_with_depth_data() -> None:
    """Test decision generation with liquidity depth data."""
    sizer = Sizer(
        edge_min=0.05,
        fee_bp=50,
        slippage_bp=30,
        kelly_cap=0.20,
        per_market_cap=1000.0,
        liquidity_min_usd=500.0,
    )
    
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    prob = BracketProb(
        bracket=bracket,
        p_zeus=0.70,
        p_mkt=0.50,
        sigma_z=2.0,
    )
    
    # Provide depth data
    depth_data = {
        "m1": MarketDepth(
            token_id="m1",
            bid_depth_usd=2000.0,
            ask_depth_usd=2500.0,
            spread_bps=50.0,
            mid_price=0.50,
        )
    }
    
    decisions = sizer.decide([prob], bankroll_usd=1000.0, depth_data=depth_data)
    
    assert len(decisions) == 1
    # Should include liquidity info
    assert decisions[0].size_usd > 0


def test_edge_sensitivity() -> None:
    """Test edge calculation sensitivity to parameters."""
    # Base case
    sizer_base = Sizer(fee_bp=50, slippage_bp=30)
    edge_base = sizer_base.compute_edge(0.60, 0.50)
    
    # Higher fees
    sizer_high_fees = Sizer(fee_bp=100, slippage_bp=30)
    edge_high_fees = sizer_high_fees.compute_edge(0.60, 0.50)
    
    # Higher slippage
    sizer_high_slip = Sizer(fee_bp=50, slippage_bp=60)
    edge_high_slip = sizer_high_slip.compute_edge(0.60, 0.50)
    
    # Higher costs should reduce edge
    assert edge_high_fees < edge_base
    assert edge_high_slip < edge_base


def test_kelly_capping_logic() -> None:
    """Test that Kelly cap is applied correctly."""
    sizer = Sizer(kelly_cap=0.10, per_market_cap=10000.0)
    
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    prob = BracketProb(
        bracket=bracket,
        p_zeus=0.90,  # Very high confidence
        p_mkt=0.50,
        sigma_z=2.0,
    )
    
    decisions = sizer.decide([prob], bankroll_usd=1000.0)
    
    assert len(decisions) == 1
    # Should be capped at 10% * $1000 = $100
    assert decisions[0].size_usd == pytest.approx(100.0, abs=0.01)
    assert "kelly_capped" in decisions[0].reason


def test_decide_reason_field() -> None:
    """Test that decision reason field is populated."""
    sizer = Sizer(edge_min=0.01, fee_bp=10, slippage_bp=10, kelly_cap=0.10)
    
    bracket = MarketBracket(name="59-60°F", lower_F=59, upper_F=60, market_id="m1")
    prob = BracketProb(
        bracket=bracket,
        p_zeus=0.65,
        p_mkt=0.50,
        sigma_z=2.0,
    )
    
    decisions = sizer.decide([prob], bankroll_usd=1000.0)
    
    assert len(decisions) == 1
    assert isinstance(decisions[0].reason, str)
    assert len(decisions[0].reason) > 0

