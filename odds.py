import requests
from datetime import timedelta
from config import ODDS_API_KEY, SUPPORTED_SPORTS, MIN_START_MINUTES, MAX_START_MINUTES
from utils import now_kst, start_in_minutes, safe_float, market_average

def valid_start_time(starts_at):
    mins = start_in_minutes(starts_at)
    if mins is None:
        return False
    return MIN_START_MINUTES <= mins <= MAX_START_MINUTES

def demo_games(sport="all"):
    now = now_kst()
    games = [
        {
            "sport": "baseball",
            "league": "KBO Demo",
            "home": "LG",
            "away": "두산",
            "starts_at": (now + timedelta(minutes=42)).isoformat(),
            "markets": [
                {"pick": "LG 승", "type": "h2h", "odds": 1.70, "open_odds": 1.82, "pinnacle_odds": 1.68, "market_avg": 1.76, "bookmaker": "Pinnacle", "is_pinnacle": True},
                {"pick": "두산 승", "type": "h2h", "odds": 2.12, "open_odds": 2.02, "pinnacle_odds": 2.12, "market_avg": 2.08, "bookmaker": "Pinnacle", "is_pinnacle": True},
            ],
        },
        {
            "sport": "soccer",
            "league": "EPL Demo",
            "home": "Arsenal",
            "away": "Chelsea",
            "starts_at": (now + timedelta(minutes=55)).isoformat(),
            "markets": [
                {"pick": "Arsenal", "type": "h2h", "odds": 1.78, "open_odds": 1.91, "pinnacle_odds": 1.74, "market_avg": 1.84, "bookmaker": "Pinnacle", "is_pinnacle": True},
                {"pick": "Draw", "type": "h2h", "odds": 3.45, "open_odds": 3.30, "pinnacle_odds": 3.42, "market_avg": 3.50, "bookmaker": "Bet365", "is_pinnacle": False},
                {"pick": "Chelsea", "type": "h2h", "odds": 4.20, "open_odds": 4.00, "pinnacle_odds": 4.18, "market_avg": 4.10, "bookmaker": "Bet365", "is_pinnacle": False},
            ],
        },
    ]
    if sport != "all":
        games = [g for g in games if g["sport"] == sport]
    return [g for g in games if valid_start_time(g.get("starts_at"))]

def sport_keys(sport):
    keys = []
    if sport == "all":
        for items in SUPPORTED_SPORTS.values():
            keys.extend(items)
        return keys
    return SUPPORTED_SPORTS.get(sport, [])

def fetch_odds_api_games(sport="all"):
    if not ODDS_API_KEY:
        return None

    games = []
    for sport_name, sport_key in sport_keys(sport):
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
        params = {"apiKey": ODDS_API_KEY, "regions": "us,eu,uk", "markets": "h2h", "oddsFormat": "decimal"}

        try:
            res = requests.get(url, params=params, timeout=12)
        except Exception:
            continue

        if res.status_code != 200:
            continue

        for item in res.json():
            starts_at = item.get("commence_time")
            if not valid_start_time(starts_at):
                continue

            outcome_map = {}
            for bookmaker in item.get("bookmakers", []):
                title = bookmaker.get("title", "Unknown")
                is_pinnacle = "pinnacle" in title.lower()

                for market in bookmaker.get("markets", []):
                    if market.get("key") != "h2h":
                        continue
                    for outcome in market.get("outcomes", []):
                        pick = outcome.get("name")
                        price = safe_float(outcome.get("price"))
                        if not pick or price <= 1:
                            continue

                        key = pick.lower().strip()
                        row = outcome_map.setdefault(key, {
                            "pick": pick, "all_odds": [], "pinnacle_odds": None,
                            "best_odds": price, "best_bookmaker": title, "bookmakers": []
                        })

                        row["all_odds"].append(price)
                        row["bookmakers"].append({"bookmaker": title, "odds": price})

                        if price > row["best_odds"]:
                            row["best_odds"] = price
                            row["best_bookmaker"] = title

                        if is_pinnacle:
                            row["pinnacle_odds"] = price

            markets = []
            for row in outcome_map.values():
                avg = market_average(row["all_odds"])
                current = safe_float(row["pinnacle_odds"]) or safe_float(row["best_odds"])
                open_proxy = round((avg or current) * 1.025, 2)

                markets.append({
                    "pick": row["pick"], "type": "h2h", "odds": current, "open_odds": open_proxy,
                    "pinnacle_odds": row["pinnacle_odds"], "market_avg": avg,
                    "best_odds": row["best_odds"], "bookmaker": "Pinnacle" if row["pinnacle_odds"] else row["best_bookmaker"],
                    "is_pinnacle": bool(row["pinnacle_odds"]), "bookmakers": row["bookmakers"][:12],
                    "source": "the_odds_api",
                })

            if markets:
                games.append({
                    "sport": sport_name, "league": sport_key, "home": item.get("home_team"),
                    "away": item.get("away_team"), "starts_at": starts_at,
                    "start_in_minutes": start_in_minutes(starts_at), "markets": markets,
                })

    return games or None

def get_games(sport="all"):
    try:
        live = fetch_odds_api_games(sport)
        if live:
            return live, "live", f"실시간 Odds API 사용 / {MIN_START_MINUTES}~{MAX_START_MINUTES}분 경기만 분석"
    except Exception as e:
        print("Odds API error:", e)

    return demo_games(sport), "demo", "실시간 API 실패 또는 키 없음. 데모 데이터 사용 중"
