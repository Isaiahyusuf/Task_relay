from datetime import datetime, timezone
from zoneinfo import ZoneInfo


AU_TZ = ZoneInfo("Australia/Sydney")


def now_au_naive() -> datetime:
    # Keep DB compatibility with naive DateTime columns while using AU local clock.
    return datetime.now(AU_TZ).replace(tzinfo=None)


def to_au(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Existing stored values are UTC-naive in this project.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(AU_TZ)


def format_au(dt: datetime | None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    local_dt = to_au(dt)
    if not local_dt:
        return "N/A"
    return local_dt.strftime(fmt)
