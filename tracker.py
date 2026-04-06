import time
from aqt import mw


def get_my_reviews() -> dict:
    """
    Returns {date_str: card_count} for the past 90 days.
    date_str format: 'YYYY-MM-DD'
    """
    if not mw.col:
        return {}

    cutoff_ms = (int(time.time()) - 90 * 86400) * 1000

    rows = mw.col.db.all(
        """
        SELECT CAST(id / 86400000 AS INTEGER) AS day_bucket,
               COUNT(*) AS cnt
        FROM revlog
        WHERE id > ?
        GROUP BY day_bucket
        """,
        cutoff_ms,
    )

    result = {}
    for day_bucket, cnt in rows:
        epoch_sec = day_bucket * 86400
        date_str = time.strftime("%Y-%m-%d", time.localtime(epoch_sec))
        result[date_str] = cnt

    return result


def get_today_str() -> str:
    return time.strftime("%Y-%m-%d")
