from datetime import datetime, timedelta, timezone

def get_games(sport="all"):
    now = datetime.now(timezone.utc)
    games = [
        {
            "sport": "soccer",
            "league": "EPL Demo",
            "home": "Arsenal",
            "away": "Chelsea",
            "starts_at": (now + timedelta(minutes=60)).isoformat(),
            "markets": [
                {
                    "pick": "Arsenal",
                    "type": "h2h",
                    "odds": 1.78,
                    "open_odds": 1.91,
                    "pinnacle_odds": 1.74,
                    "market_avg": 1.84,
                    "bookmaker": "Pinnacle",
                    "is_pinnacle": True
                }
            ],
        }
    ]
    return games, "demo", "odds.py 복구 완료"
