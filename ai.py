from utils import safe_float, implied_probability, drop_rate


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def realistic_probability(score):
    score = safe_float(score)
    if score <= 0:
        return 0
    return min(0.78, max(0.42, score / 130))


def ev_percent_from_prob(probability, odds):
    odds = safe_float(odds)
    probability = safe_float(probability)

    if odds <= 1 or probability <= 0:
        return 0

    p = probability / 100
    return round((p * odds - 1) * 100, 2)


def kelly_percent_from_prob(probability, odds):
    odds = safe_float(odds)
    probability = safe_float(probability)

    if odds <= 1 or probability <= 0:
        return 0

    p = probability / 100
    b = odds - 1
    k = ((b * p) - (1 - p)) / b

    return round(clamp(k * 100, 0, 12), 2)


def value_gap_component(odds, market_avg):
    odds = safe_float(odds)
    market_avg = safe_float(market_avg)

    if odds <= 1 or market_avg <= 1:
        return 0

    gap = ((market_avg - odds) / odds) * 100

    if gap >= 6:
        return 100
    if gap >= 4:
        return 85
    if gap >= 2:
        return 70
    if gap >= 1:
        return 55
    if gap >= 0:
        return 45
    return 25


def get_market_score(market, key, fallback=0):
    return safe_float(market.get(key), fallback)


def calculate_ai_score(market):
    odds = safe_float(market.get("odds"))
    open_odds = safe_float(market.get("open_odds"))
    pinnacle_odds = safe_float(market.get("pinnacle_odds"))
    market_avg = safe_float(market.get("market_avg"))

    d = drop_rate(open_odds, odds)

    steam_score = get_market_score(market, "steam_score")
    sharp_score = get_market_score(market, "sharp_score")
    clv_score = get_market_score(market, "clv_score")
    value_score = value_gap_component(odds, market_avg)

    pinnacle_score = 0
    if pinnacle_odds and market_avg and pinnacle_odds < market_avg:
        pinnacle_score = 80
    elif pinnacle_odds and odds and pinnacle_odds <= odds:
        pinnacle_score = 65
    else:
        pinnacle_score = 40

    drop_score = 0
    if d >= 8:
        drop_score = 100
    elif d >= 5:
        drop_score = 85
    elif d >= 3:
        drop_score = 70
    elif d >= 1:
        drop_score = 55
    else:
        drop_score = 35

    score = (
        steam_score * 0.20
        + sharp_score * 0.25
        + clv_score * 0.15
        + value_score * 0.15
        + pinnacle_score * 0.15
        + drop_score * 0.10
    )

    return int(clamp(round(score), 0, 99))


def risk_level(score, ev, kelly, ai_edge):
    if score >= 88 and ev >= 5 and kelly >= 2 and ai_edge >= 3:
        return "low"
    if score >= 76 and ev >= 0 and ai_edge >= 0:
        return "medium"
    return "high"


def recommendation_decision(confidence, ev, kelly, ai_edge, risk):
    if risk == "low" and confidence >= 88 and ev >= 5 and kelly >= 2:
        return "BET"
    if confidence >= 76 and ev >= 0 and ai_edge >= 0:
        return "WATCH"
    return "NO_BET"


def recommendation_grade(confidence, decision):
    if decision == "NO_BET":
        return "No Bet"
    if confidence >= 94:
        return "★★★★★★ S급"
    if confidence >= 88:
        return "★★★★★ A급"
    if confidence >= 80:
        return "★★★★ B급"
    return "★★★ 관찰"


def reasons_for_pick(market, d, ev, sharp_score, steam_score, clv_score, value_score, risk, confidence, ai_edge, decision):
    reasons = []

    if decision == "NO_BET":
        if ev < 0:
            reasons.append("EV 부족")
        if ai_edge < 0:
            reasons.append("AI Edge 부족")
        if risk == "high":
            reasons.append("위험도 높음")
        if sharp_score < 50:
            reasons.append("Sharp 신호 약함")
        return reasons or ["추천 근거 부족"]

    if d >= 5:
        reasons.append("초기배당 대비 강한 하락")
    elif d >= 2:
        reasons.append("배당 하락 감지")

    if sharp_score >= 80:
        reasons.append("Sharp Money 강함")
    elif sharp_score >= 60:
        reasons.append("Sharp Money 양호")

    if steam_score >= 80:
        reasons.append("Steam Move 강함")
    elif steam_score >= 60:
        reasons.append("Steam Move 감지")

    if clv_score >= 75:
        reasons.append("CLV 기대값 높음")

    if value_score >= 70:
        reasons.append("시장 평균 대비 가치 있음")

    if ev >= 10:
        reasons.append("EV 매우 우수")
    elif ev >= 5:
        reasons.append("EV 우수")
    elif ev > 0:
        reasons.append("EV 양호")

    if ai_edge >= 6:
        reasons.append("AI Edge 우수")

    if confidence >= 88:
        reasons.append("AI 신뢰도 높음")

    return reasons or ["관찰 필요"]


def ai_analysis_text(p):
    if p["decision"] == "BET":
        return (
            f"{p['pick']}은 시장 암시확률 {p['market_probability']}% 대비 "
            f"AI 예상승률 {p['ai_probability']}%로 Edge {p['ai_edge']}%입니다. "
            f"Sharp {p['sharp_score']}점, Steam {p['steam_score']}점, CLV {p['clv_score']}점으로 "
            f"실전 배팅 후보입니다."
        )

    if p["decision"] == "WATCH":
        return (
            f"{p['pick']}은 조건은 나쁘지 않지만 강한 확신은 부족합니다. "
            f"AI Edge {p['ai_edge']}%, EV {p['ev']}%라 관찰이 적절합니다."
        )

    return (
        f"{p['pick']}은 현재 No Bet입니다. "
        f"EV {p['ev']}%, AI Edge {p['ai_edge']}%, 위험도 {p['risk']} 기준에서 "
        f"추천 근거가 부족합니다."
    )


def analyze_market(game, market):
    odds = safe_float(market.get("odds"))
    open_odds = safe_float(market.get("open_odds"))
    pinnacle_odds = safe_float(market.get("pinnacle_odds"))
    market_avg = safe_float(market.get("market_avg"))

    d = drop_rate(open_odds, odds)

    score = calculate_ai_score(market)

    ai_prob = round(realistic_probability(score) * 100, 2)
    market_prob = implied_probability(odds)
    ai_edge = round(ai_prob - market_prob, 2)

    ev = ev_percent_from_prob(ai_prob, odds)
    kelly = kelly_percent_from_prob(ai_prob, odds)

    sharp_score = safe_float(market.get("sharp_score"))
    steam_score = safe_float(market.get("steam_score"))
    clv_score = safe_float(market.get("clv_score"))
    value_score = value_gap_component(odds, market_avg)

    risk = risk_level(score, ev, kelly, ai_edge)

    confidence = int(clamp(score + (ai_edge * 0.4) + (ev * 0.25), 0, 99))
    decision = recommendation_decision(confidence, ev, kelly, ai_edge, risk)

    item = {
        "sport": game.get("sport"),
        "league": game.get("league"),
        "game": f"{game.get('league')} {game.get('home')} vs {game.get('away')}",
        "home": game.get("home"),
        "away": game.get("away"),
        "starts_at": game.get("starts_at"),
        "start_in_minutes": game.get("start_in_minutes"),

        "type": market.get("type"),
        "pick": market.get("pick"),
        "bookmaker": market.get("bookmaker"),
        "is_pinnacle": market.get("is_pinnacle", False),

        "odds": odds,
        "open_odds": open_odds,
        "pinnacle_odds": pinnacle_odds,
        "market_avg": market_avg,
        "best_odds": market.get("best_odds"),

        "drop_rate": d,
        "market_probability": market_prob,
        "implied_probability": market_prob,
        "ai_probability": ai_prob,
        "ai_edge": ai_edge,

        "score": score,
        "confidence": confidence,
        "ev": ev,
        "kelly": kelly,

        "sharp_score": sharp_score,
        "steam_score": steam_score,
        "clv_score": clv_score,
        "value_score": value_score,

        "risk": risk,
        "decision": decision,
        "grade": recommendation_grade(confidence, decision),
        "bookmakers": market.get("bookmakers", []),
        "movement": market.get("movement", "-"),
        "market_count": market.get("market_count", 0),
    }

    item["reasons"] = reasons_for_pick(
        market,
        d,
        ev,
        sharp_score,
        steam_score,
        clv_score,
        value_score,
        risk,
        confidence,
        ai_edge,
        decision,
    )

    item["ai_analysis"] = ai_analysis_text(item)

    return item
