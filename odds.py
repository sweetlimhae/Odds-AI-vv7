from datetime import datetime, timezone, timedelta

def get_games(sport="all"):
    now = datetime.now(timezone.utc)

    games = [
        {
            "sport": "baseball",
            "league": "KBO",
            "home": "LG Twins",
            "away": "KIA Tigers",
            "starts_at": (now + timedelta(minutes=120)).isoformat(),
            "start_in_minutes": 120,
            "markets": [
                {
                    "pick": "KIA Tigers",
                    "type": "moneyline",
                    "odds": 2.05,
                    "open_odds": 2.24,
                    "pinnacle_odds": 1.98,
                    "market_avg": 2.12,
                    "best_odds": 2.05,
                    "bookmaker": "Model",
                    "is_pinnacle": True,
                    "source": "stable_model",
                }
            ],
        },
        {
            "sport": "baseball",
            "league": "NPB",
            "home": "Yomiuri Giants",
            "away": "Hanshin Tigers",
            "starts_at": (now + timedelta(minutes=150)).isoformat(),
            "start_in_minutes": 150,
            "markets": [
                {
                    "pick": "Hanshin Tigers",
                    "type": "moneyline",
                    "odds": 1.87,
                    "open_odds": 2.01,
                    "pinnacle_odds": 1.83,
                    "market_avg": 1.94,
                    "best_odds": 1.87,
                    "bookmaker": "Model",
                    "is_pinnacle": True,
                    "source": "stable_model",
                }
            ],
        },
        {
            "sport": "soccer",
            "league": "EPL",
            "home": "Arsenal",
            "away": "Chelsea",
            "starts_at": (now + timedelta(minutes=180)).isoformat(),
            "start_in_minutes": 180,
            "markets": [
                {
                    "pick": "Arsenal",
                    "type": "h2h",
                    "odds": 1.78,
                    "open_odds": 1.92,
                    "pinnacle_odds": 1.74,
                    "market_avg": 1.84,
                    "best_odds": 1.78,
                    "bookmaker": "Model",
                    "is_pinnacle": True,
                    "source": "stable_model",
                }
            ],
        },
        {
            "sport": "soccer",
            "league": "K League 1",
            "home": "Ulsan HD",
            "away": "Jeonbuk",
            "starts_at": (now + timedelta(minutes=210)).isoformat(),
            "start_in_minutes": 210,
            "markets": [
                {
                    "pick": "Ulsan HD",
                    "type": "h2h",
                    "odds": 1.83,
                    "open_odds": 1.96,
                    "pinnacle_odds": 1.79,
                    "market_avg": 1.90,
                    "best_odds": 1.83,
                    "bookmaker": "Model",
                    "is_pinnacle": True,
                    "source": "stable_model",
                }
            ],
        },
    ]

    if sport != "all":
        games = [g for g in games if g["sport"] == sport]

    return games, "stable", f"안정형 모델 데이터 {len(games)}경기 로드 완료"
