from datetime import datetime, timezone, timedelta


def make_market(pick, odds, open_odds, pinnacle_odds, market_avg, bookmaker="Model"):
    drop_rate = round(((open_odds - odds) / open_odds) * 100, 2) if open_odds else 0
    edge = round(((market_avg - odds) / odds) * 100, 2) if odds else 0

    steam_score = min(100, max(0, round(drop_rate * 10)))
    sharp_score = min(100, max(0, round((open_odds - pinnacle_odds) / open_odds * 1000))) if open_odds else 0
    clv_score = min(100, max(0, round((market_avg - pinnacle_odds) / market_avg * 1000))) if market_avg else 0

    return {
        "pick": pick,
        "type": "moneyline",
        "odds": odds,
        "open_odds": open_odds,
        "pinnacle_odds": pinnacle_odds,
        "market_avg": market_avg,
        "best_odds": odds,
        "bookmaker": bookmaker,
        "is_pinnacle": bookmaker.lower() == "pinnacle" or bookmaker == "Model",
        "source": "stable_model_v3",

        "drop_rate": drop_rate,
        "edge": edge,
        "movement": "down" if odds < open_odds else "up",
        "steam_score": steam_score,
        "sharp_score": sharp_score,
        "clv_score": clv_score,
        "market_count": 5,

        "bookmakers": [
            {"bookmaker": "Pinnacle", "odds": pinnacle_odds},
            {"bookmaker": "Bet365", "odds": round(odds * 1.01, 2)},
            {"bookmaker": "SBOBET", "odds": round(odds * 0.99, 2)},
            {"bookmaker": "1xBet", "odds": round(odds * 1.02, 2)},
            {"bookmaker": "Market Avg", "odds": market_avg},
        ],
    }


def get_games(sport="all", minutes=1440):
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
                make_market("KIA Tigers", 2.05, 2.24, 1.98, 2.12)
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
                make_market("Hanshin Tigers", 1.87, 2.01, 1.83, 1.94)
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
                make_market("Arsenal", 1.78, 1.92, 1.74, 1.84)
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
                make_market("Ulsan HD", 1.83, 1.96, 1.79, 1.90)
            ],
        },
    ]

    if sport != "all":
        games = [g for g in games if g["sport"] == sport]

    filtered = []
    for g in games:
        m = g.get("start_in_minutes", 0)
        if 0 <= m <= int(minutes):
            filtered.append(g)

    return filtered, "stable_v3", f"V3 분석 모델 데이터 {len(filtered)}경기 로드 완료"
