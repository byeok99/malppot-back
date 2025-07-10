from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    HAS_ZONEINFO = True
except ImportError:
    HAS_ZONEINFO = False

KST = timezone(timedelta(hours=9))


def now_kst():
    """한국 시간(KST)으로 현재 datetime 반환"""
    if HAS_ZONEINFO:
        return datetime.now(ZoneInfo("Asia/Seoul"))
    else:
        return datetime.now(KST)


def today_kst():
    """한국 시간(KST) 기준 오늘 날짜 반환"""
    return now_kst().date()
