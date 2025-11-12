"""Timezone and datetime utilities.

DST-aware helpers for converting between local market times and UTC.
"""

from datetime import datetime, time, timedelta
from typing import Tuple

import pytz
from dateutil import tz


def get_local_day_window_utc(
    date_local: datetime.date, timezone_name: str
) -> Tuple[datetime, datetime]:
    """Get UTC start/end timestamps for a local calendar day.

    Handles DST transitions correctly by using the local timezone.

    Args:
        date_local: The calendar date in local time
        timezone_name: IANA timezone name (e.g., 'America/New_York')

    Returns:
        Tuple of (start_utc, end_utc) for the 24-hour local day
    """
    local_tz = pytz.timezone(timezone_name)

    # Start of day (00:00) in local time
    start_local = local_tz.localize(datetime.combine(date_local, time.min))
    start_utc = start_local.astimezone(pytz.utc)

    # End of day (23:59:59.999999) in local time
    end_local = local_tz.localize(
        datetime.combine(date_local, time.max)
    )
    end_utc = end_local.astimezone(pytz.utc)

    return start_utc, end_utc


def utc_to_local(dt_utc: datetime, timezone_name: str) -> datetime:
    """Convert UTC datetime to local timezone.

    Args:
        dt_utc: UTC datetime (must be timezone-aware or assumed UTC)
        timezone_name: IANA timezone name

    Returns:
        Datetime in local timezone
    """
    if dt_utc.tzinfo is None:
        dt_utc = pytz.utc.localize(dt_utc)

    local_tz = pytz.timezone(timezone_name)
    return dt_utc.astimezone(local_tz)


def local_to_utc(dt_local: datetime, timezone_name: str) -> datetime:
    """Convert local datetime to UTC.

    Args:
        dt_local: Local datetime (naive or timezone-aware)
        timezone_name: IANA timezone name

    Returns:
        UTC datetime
    """
    local_tz = pytz.timezone(timezone_name)

    if dt_local.tzinfo is None:
        dt_local = local_tz.localize(dt_local)

    return dt_local.astimezone(pytz.utc)


def is_dst(dt: datetime, timezone_name: str) -> bool:
    """Check if a datetime is in daylight saving time.

    Args:
        dt: Datetime to check (UTC or local)
        timezone_name: IANA timezone name

    Returns:
        True if DST is active, False otherwise
    """
    local_tz = pytz.timezone(timezone_name)

    if dt.tzinfo is None:
        dt = local_tz.localize(dt)
    else:
        dt = dt.astimezone(local_tz)

    return dt.dst() != timedelta(0)

