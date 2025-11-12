"""Tests for timezone and datetime utilities.

Stage 1 implementation - comprehensive time utility tests including DST.
"""

import pytest
from datetime import datetime, date, timezone
from core import time_utils


def test_local_day_window_utc_london() -> None:
    """Test local day window for London timezone."""
    # January (GMT, no DST)
    test_date = date(2025, 1, 15)
    start, end = time_utils.get_local_day_window_utc(test_date, "Europe/London")
    
    # Should be midnight to 23:59:59.999999 in London (which is same as UTC in winter)
    assert start.hour == 0
    assert start.minute == 0
    assert end.hour == 23
    assert end.minute == 59


def test_local_day_window_utc_newyork() -> None:
    """Test local day window for New York timezone."""
    # January (EST, UTC-5)
    test_date = date(2025, 1, 15)
    start, end = time_utils.get_local_day_window_utc(test_date, "America/New_York")
    
    # Local midnight in NY = 05:00 UTC
    assert start.hour == 5
    assert start.minute == 0
    
    # Local 23:59:59 in NY = next day 04:59:59 UTC
    assert end.day == 16  # Next day in UTC
    assert end.hour == 4
    assert end.minute == 59


def test_local_day_window_utc_dst_transition_spring() -> None:
    """Test local day window during spring DST transition (clocks forward).

    In 2025, US DST starts March 9 at 2:00 AM → 3:00 AM
    This is a 23-hour day locally.
    """
    # Day of spring forward in New York
    test_date = date(2025, 3, 9)
    start, end = time_utils.get_local_day_window_utc(test_date, "America/New_York")
    
    # Should handle the transition correctly
    assert start.tzinfo is not None
    assert end.tzinfo is not None
    
    # Verify we get a valid window
    assert end > start


def test_local_day_window_utc_dst_transition_fall() -> None:
    """Test local day window during fall DST transition (clocks back).

    In 2025, US DST ends November 2 at 2:00 AM → 1:00 AM
    This is a 25-hour day locally.
    """
    # Day of fall back in New York
    test_date = date(2025, 11, 2)
    start, end = time_utils.get_local_day_window_utc(test_date, "America/New_York")
    
    # Should handle the transition correctly
    assert start.tzinfo is not None
    assert end.tzinfo is not None
    
    # Verify we get a valid window
    assert end > start


def test_utc_to_local() -> None:
    """Test UTC to local timezone conversion."""
    # Noon UTC on January 15, 2025
    dt_utc = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    
    # Convert to New York (EST, UTC-5)
    dt_ny = time_utils.utc_to_local(dt_utc, "America/New_York")
    assert dt_ny.hour == 7  # 12 - 5 = 7 AM
    assert dt_ny.day == 15
    
    # Convert to Tokyo (JST, UTC+9)
    dt_tokyo = time_utils.utc_to_local(dt_utc, "Asia/Tokyo")
    assert dt_tokyo.hour == 21  # 12 + 9 = 21 (9 PM)
    assert dt_tokyo.day == 15


def test_local_to_utc() -> None:
    """Test local to UTC timezone conversion."""
    # 3 PM EST on January 15, 2025
    from pytz import timezone as pytz_tz
    
    eastern = pytz_tz("America/New_York")
    dt_local = eastern.localize(datetime(2025, 1, 15, 15, 0, 0))
    
    dt_utc = time_utils.local_to_utc(dt_local, "America/New_York")
    assert dt_utc.hour == 20  # 15 + 5 = 20 (8 PM UTC)
    assert dt_utc.day == 15


def test_local_to_utc_naive_datetime() -> None:
    """Test local to UTC with naive datetime (no tzinfo)."""
    # Naive datetime (no timezone info)
    dt_naive = datetime(2025, 1, 15, 15, 0, 0)
    
    # Should localize to Eastern then convert to UTC
    dt_utc = time_utils.local_to_utc(dt_naive, "America/New_York")
    assert dt_utc.hour == 20  # 15 + 5 = 20 (8 PM UTC)
    assert dt_utc.tzinfo is not None


def test_is_dst_true() -> None:
    """Test DST detection when DST is active."""
    # July in New York (EDT, DST active)
    from pytz import timezone as pytz_tz
    eastern = pytz_tz("America/New_York")
    dt_summer = eastern.localize(datetime(2025, 7, 15, 12, 0, 0))
    
    assert time_utils.is_dst(dt_summer, "America/New_York") is True


def test_is_dst_false() -> None:
    """Test DST detection when DST is not active."""
    # January in New York (EST, no DST)
    from pytz import timezone as pytz_tz
    eastern = pytz_tz("America/New_York")
    dt_winter = eastern.localize(datetime(2025, 1, 15, 12, 0, 0))
    
    assert time_utils.is_dst(dt_winter, "America/New_York") is False


def test_is_dst_utc_input() -> None:
    """Test DST detection with UTC input."""
    # UTC time that corresponds to EDT period
    dt_utc = datetime(2025, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
    
    # Should convert to NY time and detect DST
    assert time_utils.is_dst(dt_utc, "America/New_York") is True


def test_timezone_boundaries_cross_date() -> None:
    """Test that timezone conversions handle date boundaries correctly."""
    # 11 PM in New York
    from pytz import timezone as pytz_tz
    eastern = pytz_tz("America/New_York")
    dt_local = eastern.localize(datetime(2025, 1, 15, 23, 0, 0))
    
    # Convert to UTC (should be next day)
    dt_utc = time_utils.local_to_utc(dt_local, "America/New_York")
    assert dt_utc.day == 16
    assert dt_utc.hour == 4  # 23 + 5 = 28, which is 4 AM next day


def test_roundtrip_conversion() -> None:
    """Test roundtrip UTC → Local → UTC preserves datetime."""
    dt_original = datetime(2025, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
    
    # Convert to local and back
    dt_local = time_utils.utc_to_local(dt_original, "America/Chicago")
    dt_back = time_utils.local_to_utc(dt_local, "America/Chicago")
    
    # Should be equal (accounting for microsecond precision)
    assert abs((dt_back - dt_original).total_seconds()) < 1


def test_multiple_timezones() -> None:
    """Test conversions across multiple timezones."""
    timezones = [
        "America/New_York",
        "America/Chicago", 
        "America/Los_Angeles",
        "Europe/London",
        "Asia/Tokyo",
        "Australia/Sydney",
    ]
    
    dt_utc = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    
    for tz_name in timezones:
        # Convert to local
        dt_local = time_utils.utc_to_local(dt_utc, tz_name)
        assert dt_local.tzinfo is not None
        
        # Convert back to UTC
        dt_back = time_utils.local_to_utc(dt_local, tz_name)
        
        # Should match original (within 1 second)
        assert abs((dt_back - dt_utc).total_seconds()) < 1


def test_london_dst_boundary() -> None:
    """Test London timezone around DST boundaries.

    UK DST 2025: March 30 (spring forward) and October 26 (fall back)
    """
    # Day before spring DST
    test_date = date(2025, 3, 29)
    start, end = time_utils.get_local_day_window_utc(test_date, "Europe/London")
    assert start.tzinfo is not None
    
    # Day of spring DST
    test_date = date(2025, 3, 30)
    start, end = time_utils.get_local_day_window_utc(test_date, "Europe/London")
    assert start.tzinfo is not None
    
    # Day of fall DST
    test_date = date(2025, 10, 26)
    start, end = time_utils.get_local_day_window_utc(test_date, "Europe/London")
    assert start.tzinfo is not None

