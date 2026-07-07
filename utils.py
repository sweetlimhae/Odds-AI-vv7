from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default

def now_kst():
    return datetime.now(KST)

def start_in_minutes(starts_at):
    if not starts_at:
        return None
    try:
        start = datetime.fromisoformat(str(starts_at).replace("Z", "+00:00"))
        return int((start - datetime.now(timezone.utc)).total_seconds() // 60)
    except Exception:
        try:
            start = datetime.fromisoformat(str(starts_at))
            return int((start - now_kst()).total_seconds() // 60)
        except Exception:
            return None

def implied_probability(odds):
    odds = safe_float(odds)
    if odds <= 1:
        return 0
    return round((1 / odds) * 100, 2)

def drop_rate(open_odds, current_odds):
    open_odds = safe_float(open_odds)
    current_odds = safe_float(current_odds)
    if open_odds <= 1 or current_odds <= 1:
        return 0
    return round(((open_odds - current_odds) / open_odds) * 100, 2)

def market_average(values):
    nums = [safe_float(v) for v in values if safe_float(v) > 1]
    if not nums:
        return 0
    return round(sum(nums) / len(nums), 3)
