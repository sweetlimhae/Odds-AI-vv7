from itertools import combinations
import math
from utils import safe_float
from ai import analyze_market

def flatten_picks(games):
    picks = []
    for game in games or []:
        for market in game.get("markets", []):
            if safe_float(market.get("odds")) > 1:
                picks.append(analyze_market(game, market))

    return sorted(
        picks,
        key=lambda p: (p["decision"] == "BET", p["confidence"], p["ai_edge"], p["ev"]),
        reverse=True
    )

def make_combo(name, picks, size):
    candidates = picks[:14]
    best = None

    for combo in combinations(candidates, size):
        game_names = [p["game"] for p in combo]
        if len(set(game_names)) != len(game_names):
            continue

        total_odds = math.prod([safe_float(p["odds"], 1) for p in combo])
        avg_score = sum(p["score"] for p in combo) / size
        avg_confidence = sum(p["confidence"] for p in combo) / size
        avg_ev = sum(p["ev"] for p in combo) / size
        avg_kelly = sum(p["kelly"] for p in combo) / size
        avg_edge = sum(p["ai_edge"] for p in combo) / size

        item = {
            "type": name, "folder_size": size, "total_odds": round(total_odds, 2),
            "avg_score": round(avg_score, 1), "avg_confidence": round(avg_confidence, 1),
            "avg_ev": round(avg_ev, 2), "avg_kelly": round(avg_kelly, 2),
            "avg_edge": round(avg_edge, 2), "picks": list(combo),
        }

        rank = (item["avg_confidence"], item["avg_edge"], item["avg_ev"], item["avg_score"])
        if best is None or rank > (best["avg_confidence"], best["avg_edge"], best["avg_ev"], best["avg_score"]):
            best = item

    return best

def build_recommendations(games):
    picks = flatten_picks(games)
    bet = [p for p in picks if p["decision"] == "BET"]
    watch = [p for p in picks if p["decision"] in ["BET", "WATCH"]]

    combos = []
    for size in [2, 3, 4]:
        if len(bet) >= size:
            combos.append(make_combo(f"실전형 {size}폴더", bet, size))
        if len(watch) >= size:
            combos.append(make_combo(f"관찰형 {size}폴더", watch, size))

    combos = [c for c in combos if c]
    combos = sorted(combos, key=lambda c: (c["avg_confidence"], c["avg_edge"], c["avg_ev"]), reverse=True)
    return combos[:9], picks, len(combos) == 0

def build_summary(picks, combos, no_bet):
    if not picks:
        return {
            "total_picks": 0, "top_score": 0, "top_confidence": 0,
            "avg_ev": 0, "avg_edge": 0, "recommendation_count": 0,
            "no_bet": True, "message": "분석 가능한 경기가 없습니다.",
        }

    bet_count = len([p for p in picks if p["decision"] == "BET"])
    watch_count = len([p for p in picks if p["decision"] == "WATCH"])
    no_bet_count = len([p for p in picks if p["decision"] == "NO_BET"])

    return {
        "total_picks": len(picks), "bet_count": bet_count, "watch_count": watch_count,
        "no_bet_count": no_bet_count, "top_score": max(p["score"] for p in picks),
        "top_confidence": max(p["confidence"] for p in picks),
        "avg_ev": round(sum(p["ev"] for p in picks) / len(picks), 2),
        "avg_edge": round(sum(p["ai_edge"] for p in picks) / len(picks), 2),
        "recommendation_count": len(combos), "no_bet": no_bet,
        "message": "추천 가능" if not no_bet else "오늘은 무리한 배팅보다 관망을 추천합니다.",
    }
