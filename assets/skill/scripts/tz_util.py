"""The operator's time zone: the single source for labels and day keys.

DLMM_TZ (an IANA name such as "UTC" or "Europe/Berlin", set in the profile .env)
selects the zone every report card is labelled in and every daily bucket is cut
in (Redis daily keys, the daily scoreboard send). Unset, empty or unknown means
UTC, so two hosts with the same config agree regardless of their system zone.
Timestamps are still stored as UTC epochs; this only decides how they are shown
and which calendar day they count towards. %Z renders the zone label, so a card
never shows a bare local time.
"""
import os
from datetime import datetime, timezone


def zone():
    """The configured zone, or UTC when DLMM_TZ is unset or not a known zone."""
    name = os.environ.get("DLMM_TZ", "").strip()
    if not name:
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:
        # Unknown zone name or missing tzdata: never break a report card.
        return timezone.utc


def zone_name():
    """IANA name of the zone in use ("UTC" for the fallback)."""
    return getattr(zone(), "key", None) or "UTC"


def local_dt(ts=None):
    """Aware datetime in the configured zone, for `ts` (UTC epoch) or now."""
    if ts is None:
        return datetime.now(zone())
    return datetime.fromtimestamp(float(ts), zone())


def local_time_str(fmt="%H:%M %Z", ts=None):
    """Formatted time in the configured zone; keep %Z in `fmt` to show the zone."""
    return local_dt(ts).strftime(fmt)


def local_date_str(ts=None):
    """YYYY-MM-DD day key in the configured zone, for `ts` (UTC epoch) or now."""
    return local_dt(ts).strftime("%Y-%m-%d")
