from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
KRX_DATA_CONFIRM_HOUR = 18


def get_collectible_end_date() -> date:
    now = datetime.now(KST)
    candidate = now.date() if now.hour >= KRX_DATA_CONFIRM_HOUR else now.date() - timedelta(days=1)

    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)

    return candidate


def calc_collection_range(
    db_latest_date: str | None,
    collectible_end: date,
) -> tuple[date, date] | None:
    if db_latest_date is None:
        return (collectible_end - timedelta(days=90), collectible_end)

    latest = datetime.strptime(db_latest_date, "%Y%m%d").date()

    if latest >= collectible_end:
        return None

    return (latest + timedelta(days=1), collectible_end)
