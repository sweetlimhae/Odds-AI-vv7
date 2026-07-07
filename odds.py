import os
import requests
from datetime import datetime, timezone

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

SPORT_KEYS = {
    "soccer": [
        "soccer_epl",
        "soccer_efl_champ",
        "soccer_england_league1",
        "soccer_england_league2",
        "soccer_spain_la_liga",
        "soccer_spain_segunda_division",
        "soccer_germany_bundesliga",
        "soccer_germany_bundesliga2",
        "soccer_italy_serie_a",
        "soccer_italy_serie_b",
        "soccer_france_ligue_one",
        "soccer_france_ligue_two",
        "soccer_netherlands_eredivisie",
        "soccer_portugal_primeira_liga",
        "soccer_turkey_super_league",
        "soccer_japan_j_league",
        "soccer_korea_kleague1",
        "soccer_usa_mls",
        "soccer_mexico_ligamx",
        "soccer_brazil_campeonato",
        "soccer_argentina_primera_division",
    ],
    "baseball": [
        "baseball_mlb",
        "baseball_kbo",
        "baseball_npb",
    ],
    "basketball": [
        "basketball_nba",
        "basketball_wnba",
    ],
    "hockey": [
        "icehockey_nhl",
    ],
    "americanfootball": [
        "americanfootball_nfl",
    ],
}


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


def selected_sport_keys(sport):
    if sport == "all":
        keys = []
        for group in SPORT_KEYS.values():
            keys.extend(group)
        return keys

    return SPORT_KEYS.get(sport, [])


def fetch_one_league(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"

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
            games.append({
                "sport": "baseball" if sport_key.startswith("baseball") else "soccer" if sport_key.startswith("soccer") else "other",
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

    games = []
    errors = []

    for sport_key in selected_sport_keys(sport):
        try:
            games.extend(fetch_one_league(sport_key))
        except Exception as e:
            errors.append(f"{sport_key}: {str(e)}")

    if not games:
        if errors:
            return [], "live", "실시간 데이터 없음 / 일부 리그 오류"
        return [], "live", "현재 조건에 맞는 실시간 경기가 없습니다."

    return games, "live", f"실시간 Odds API 데이터 {len(games)}경기 로드 완료"
