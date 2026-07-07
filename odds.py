from datetime import datetime, timezone, timedelta


def avg(nums):
    nums = [n for n in nums if n and n > 1]
    return round(sum(nums) / len(nums), 2) if nums else 0


def pct_drop(open_odds, current_odds):
    if not open_odds or not current_odds:
        return 0
    return round(((open_odds - current_odds) / open_odds) * 100, 2)


def make_market(pick, open_odds, bookmakers):
    pinnacle = next((b["odds"] for b in bookmakers if b["bookmaker"].lower() == "pinnacle"), None)
    odds_values = [b["odds"] for b in bookmakers]
    market_avg = avg(odds_values)
    best = max(odds_values)

    current_odds = pinnacle or market_avg
    drop_rate = pct_drop(open_odds, current_odds)

    sharp_score = min(100, max(0, round(drop_rate * 10 + (15 if pinnacle and pinnacle < market_avg else 0))))
    steam_score = min(100, max(0, round(drop_rate * 12)))
    clv_score = min(100, max(0, round(((market_avg - current_odds) / market_avg) * 1000))) if market_avg else 0
    rlm_score = min(100, max(0, round(drop_rate * 8 + (20 if current_odds < market_avg else 0))))

    return {
        "pick": pick,
        "type": "moneyline",
        "odds": current_odds,
        "open_odds": open_odds,
        "pinnacle_odds": pinnacle,
        "market_avg": market_avg,
        "best_odds": best,
        "bookmaker": "Pinnacle" if pinnacle else "Market Avg",
        "is_pinnacle": bool(pinnacle),
        "source": "bookmaker_consensus_v1",

        "drop_rate": drop_rate,
        "movement": "down" if current_odds < open_odds else "up",
        "steam_score": steam_score,
        "sharp_score": sharp_score,
        "clv_score": clv_score,
        "rlm_score": rlm_score,
        "market_count": len(bookmakers),
        "bookmakers": bookmakers,
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
                make_market("KIA Tigers", 2.24, [
                    {"bookmaker": "Pinnacle", "odds": 1.98},
                    {"bookmaker": "Bet365", "odds": 2.05},
                    {"bookmaker": "SBOBET", "odds": 2.02},
                    {"bookmaker": "1xBet", "odds": 2.08},
                    {"bookmaker": "188Bet", "odds": 2.04},
                ])
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
                make_market("Hanshin Tigers", 2.01, [
                    {"bookmaker": "Pinnacle", "odds": 1.83},
                    {"bookmaker": "Bet365", "odds": 1.87},
                    {"bookmaker": "SBOBET", "odds": 1.86},
                    {"bookmaker": "1xBet", "odds": 1.90},
                    {"bookmaker": "188Bet", "odds": 1.88},
                ])
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
                make_market("Arsenal", 1.92, [
                    {"bookmaker": "Pinnacle", "odds": 1.74},
                    {"bookmaker": "Bet365", "odds": 1.78},
                    {"bookmaker": "SBOBET", "odds": 1.77},
                    {"bookmaker": "1xBet", "odds": 1.82},
                    {"bookmaker": "188Bet", "odds": 1.79},
                ])
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
                make_market("Ulsan HD", 1.96, [
                    {"bookmaker": "Pinnacle", "odds": 1.79},
                    {"bookmaker": "Bet365", "odds": 1.83},
                    {"bookmaker": "SBOBET", "odds": 1.82},
                    {"bookmaker": "1xBet", "odds": 1.86},
                    {"bookmaker": "188Bet", "odds": 1.84},
                ])
            ],
        },
    ]

    if sport != "all":
        games = [g for g in games if g["sport"] == sport]

    games = [g for g in games if 0 <= g["start_in_minutes"] <= int(minutes)]

    return games, "bookmaker_v1", f"북메이커 컨센서스 데이터 {len(games)}경기 로드 완료"
