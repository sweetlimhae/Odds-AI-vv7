import os
import requests
from datetime import datetime, timezone

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

BASE_URL = "https://api.the-odds-api.com/v4"

# 크레딧 아끼려고 한 번에 너무 많이 호출하지 않게 제한
MAX_LEAGUES_PER_REQUEST = 8


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def start_in_minutes(starts_at):
    try:
        start = datetime.fromisoformat(str(starts_at).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return int((start - now).total_seconds() // 60)
    except Exception:
        return None


def market_average(values):
    nums = [safe_float(v) for v in values if safe_float(v) > 1]
    if not nums:
        return 0
    return round(sum(nums) / len(nums), 3)


def get_available_sports():
    if not ODDS_API_KEY:
        return []

    try:
        r = requests.get(
            f"{BASE_URL}/sports/",
            params={"apiKey": ODDS_API_KEY},
            timeout=10
        )
        if r.status_code != 200:
            return []
        return r.json()
    except Exception:
        return []


def selected_sport_keys(sport):
    available = get_available_sports()

    if not available:
        return []

    keys = []

    if sport == "soccer":
        keys = [
            s["key"] for s in available
            if s.get("active") and s.get("key", "").startswith("soccer_")
        ]

    elif sport == "baseball":
        keys = [
            s["key"] for s in available
            if s.get("active") and s.get("key") in [
                "baseball_mlb",
                "baseball_kbo",
                "baseball_npb",
            ]
        ]

    elif sport == "basketball":
        keys = [
            s["key"] for s in available
            if s.get("active") and s.get("key") in [
                "basketball_nba",
                "basketball_wnba",
            ]
        ]

    elif sport == "hockey":
        keys = [
            s["key"] for s in available
            if s.get("active") and s.get("key") == "icehockey_nhl"
        ]

    elif sport == "americanfootball":
        keys = [
            s["key"] for s in available
            if s.get("active") and s.get("key") == "americanfootball_nfl"
        ]

    elif sport == "all":
        for s in available:
            key = s.get("key", "")
            if not s.get("active"):
                continue

            if (
                key.startswith("soccer_")
                or key in ["baseball_mlb", "baseball_kbo", "baseball_npb"]
                or key in ["basketball_nba", "basketball_wnba"]
                or key == "icehockey_nhl"
                or key == "americanfootball_nfl"
            ):
                keys.append(key)

    return keys[:MAX_LEAGUES_PER_REQUEST]


def fetch_one_league(sport_key):
    url = f"{BASE_URL}/sports/{sport_key}/odds"

    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us,eu,uk",
        "markets": "h2h",
        "oddsFormat": "decimal",
    }

    response = requests.get(url, params=params, timeout=12)

    if response.status_code != 200:
        return []

    data = response.json()
    games = []

    for item in data:
        outcome_map = {}

        for bookmaker in item.get("bookmakers", []):
            bookmaker_name = bookmaker.get("title", "Unknown")
            is_pinnacle = "pinnacle" in bookmaker_name.lower()

            for market in bookmaker.get("markets", []):
                if market.get("key") != "h2h":
                    continue

                for outcome in market.get("outcomes", []):
                    pick = outcome.get("name")
                    odds = safe_float(outcome.get("price"))

                    if not pick or odds <= 1:
                        continue

                    key = pick.lower().strip()

                    if key not in outcome_map:
                        outcome_map[key] = {
                            "pick": pick,
                            "type": "h2h",
                            "all_odds": [],
                            "pinnacle_odds": None,
                            "best_odds": odds,
                            "best_bookmaker": bookmaker_name,
                            "bookmakers": [],
                        }

                    row = outcome_map[key]
                    row["all_odds"].append(odds)
                    row["bookmakers"].append({
                        "bookmaker": bookmaker_name,
                        "odds": odds,
                    })

                    if odds > row["best_odds"]:
                        row["best_odds"] = odds
                        row["best_bookmaker"] = bookmaker_name

                    if is_pinnacle:
                        row["pinnacle_odds"] = odds

        markets = []

        for row in outcome_map.values():
            market_avg = market_average(row["all_odds"])
            current_odds = row["pinnacle_odds"] or row["best_odds"]
            open_odds = round((market_avg or current_odds) * 1.025, 2)

            markets.append({
                "pick": row["pick"],
                "type": row["type"],
                "odds": current_odds,
                "open_odds": open_odds,
                "pinnacle_odds": row["pinnacle_odds"],
                "market_avg": market_avg,
                "best_odds": row["best_odds"],
                "bookmaker": "Pinnacle" if row["pinnacle_odds"] else row["best_bookmaker"],
                "is_pinnacle": bool(row["pinnacle_odds"]),
                "bookmakers": row["bookmakers"][:12],
                "source": "the_odds_api",
            })

        if markets:
            if sport_key.startswith("baseball"):
                sport = "baseball"
            elif sport_key.startswith("soccer"):
                sport = "soccer"
            elif sport_key.startswith("basketball"):
                sport = "basketball"
            elif sport_key.startswith("icehockey"):
                sport = "hockey"
            elif sport_key.startswith("americanfootball"):
                sport = "americanfootball"
            else:
                sport = "other"

            games.append({
                "sport": sport,
                "league": sport_key,
                "home": item.get("home_team"),
                "away": item.get("away_team"),
                "starts_at": item.get("commence_time"),
                "start_in_minutes": start_in_minutes(item.get("commence_time")),
                "markets": markets,
            })

    return games


def get_games(sport="all"):
    if not ODDS_API_KEY:
        return [], "error", "ODDS_API_KEY가 없습니다."

    keys = selected_sport_keys(sport)

    if not keys:
        return [], "live", "활성화된 리그가 없거나 API 키 문제가 있습니다."

    games = []
    errors = []

    for sport_key in keys:
        try:
            games.extend(fetch_one_league(sport_key))
        except Exception as e:
            errors.append(f"{sport_key}: {str(e)}")

    if not games:
        return [], "live", "현재 조건에 맞는 실시간 경기가 없습니다."

    return games, "live", f"실시간 Odds API 데이터 {len(games)}경기 로드 완료"
