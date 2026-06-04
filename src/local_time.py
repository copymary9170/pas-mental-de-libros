from datetime import datetime
from zoneinfo import ZoneInfo

APP_TIMEZONE = "America/Caracas"


def today_local():
    """Return today's date in the app's intended local timezone: Venezuela."""
    return datetime.now(ZoneInfo(APP_TIMEZONE)).date()


def now_local():
    """Return current datetime in Venezuela local timezone."""
    return datetime.now(ZoneInfo(APP_TIMEZONE))
