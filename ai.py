from utils import safe_float, implied_probability, drop_rate

def realistic_probability(score):
    score = safe_float(score)
    if score <= 0:
        return 0
    return min(0.72, max(0.45, score / 135))

def ev_percent(score, odds):
    odds = safe_float(odds)
    if odds <= 1 or score <= 0:
        return 0
    p = realistic_probability(score)
    return round((p * odds - 1) * 100, 2)

def kelly_percent(score, odds):
    odds = safe_float(odds)
    if odds <= 1 or score <= 0:
        return 0
    p = realistic_probability(score)
    b = odds - 1
    k = ((b * p) - (1 - p)) / b
    return round(max(0, min(k * 100, 15)), 2)

def value_gap_component(odds, market_avg):
    odds = safe_float(odds)
    market_avg = safe_float(market_avg)
    if odds <= 1 or market_avg <= 1:
        return 0

    gap = ((odds - market_avg) / market_avg) * 100
    if gap >= 5:
        return 18
    if gap >= 3:
        return 13
    if gap >= 1.5:
        return 8
    if gap >= 0.5:
        return 4
    if gap <= -3:
        return -10
    return 0

def pinnacle_bonus(market):
    return 10 if market.get("is_pinnacle") or "pinnacle" in str(market.get("bookmaker", "")).lower() else 0

def sharp_component(open_odds, current_odds, pinnacle_odds, market_avg, market):
    d = drop_rate(open_odds, current_odds)
    score = 0

    if d >= 6:
        score += 25
    elif d >= 4:
        score += 18
    elif d >= 2:
        score += 10
    elif d >= 0.8:
        score += 5

    current = safe_float(current_odds)
    pin = safe_float(pinnacle_odds)
    avg = safe_float(market_avg)

    if pin and avg and pin < avg:
        score += 16
    elif pin and avg and pin <= avg * 1.01:
        score += 8

    if pin and current and abs(pin - current) / current < 0.015:
        score += 6

    score += pinnacle_bonus(market)
    return max(0, min(45, round(score, 1)))

def steam_component(open_odds, current_odds):
    d = drop_rate(open_odds, current_odds)
    if d >= 8:
        return 22
    if d >= 5:
        return 16
    if d >= 3:
        return 10
    if d >= 1:
        return 4
    return 0

def clv_component(current_odds, pinnacle_odds, market_avg):
    current = safe_float(current_odds)
    pin = safe_float(pinnacle_odds)
    avg = safe_float(market_avg)

    score = 0
    if pin and avg and pin < avg:
        score += 12
    if current and avg and current >= avg:
        score += 8
    if pin and current and current >= pin:
        score += 6
    return min(24, score)

def reverse_line_component(open_odds, current_odds, market_avg):
    d = drop_rate(open_odds, current_odds)
    avg = safe_float(market_avg)
    current = safe_float(current_odds)

    if d >= 2 and avg and current <= avg:
        return 8
    if d >= 1 and avg and current <= avg * 1.01:
        return 4
    return 0

def risk_level(score, ev, kelly, d, ai_edge):
    if score >= 86 and ev >= 2 and kelly > 0 and d >= 1 and ai_edge >= 2:
        return "low"
    if score >= 76 and ev >= -1 and ai_edge >= -1:
        return "medium"
    return "high"

def confidence_score(score, ev, kelly, risk, ai_edge):
    confidence = safe_float(score)

    if ai_edge >= 8:
        confidence += 6
    elif ai_edge >= 4:
        confidence += 3
    elif ai_edge < 0:
        confidence -= 8

    if ev >= 8:
        confidence += 5
    elif ev >= 3:
        confidence += 2
    elif ev < -3:
        confidence -= 8

    if kelly >= 5:
        confidence += 3
    elif kelly <= 0:
        confidence -= 4

    if risk == "low":
        confidence += 4
    elif risk == "high":
        confidence -= 10

    return int(max(0, min(99, round(confidence))))

def recommendation_decision(confidence, ev, kelly, ai_edge, risk):
    if risk == "high" or ev < -3 or ai_edge < -2:
        return "NO_BET"
    if confidence >= 88 and ev >= 3 and kelly > 0 and ai_edge >= 3:
        return "BET"
    if confidence >= 76 and ev >= 0 and ai_edge >= 0:
        return "WATCH"
    return "NO_BET"

def recommendation_grade(confidence, decision):
    if decision == "NO_BET":
        return "No Bet"
    if confidence >= 92:
        return "★★★★★ 강추천"
    if confidence >= 85:
        return "★★★★ 추천"
    if confidence >= 76:
        return "★★★ 관찰"
    return "No Bet"

def reasons_for_pick(market, d, ev, sharp, steam, clv, value_gap, risk, confidence, ai_edge, decision):
    reasons = []

    if decision == "NO_BET":
        if ev < 0:
            reasons.append("EV 부족")
        if ai_edge < 0:
            reasons.append("AI Edge 부족")
        if risk == "high":
            reasons.append("위험도 높음")
        if sharp < 12:
            reasons.append("Sharp 신호 약함")
        return reasons or ["추천 근거 부족"]

    if market.get("is_pinnacle"):
        reasons.append("Pinnacle 기준 배당 사용")
    if d >= 3:
        reasons.append("초기 대비 배당 하락")
    elif d >= 1:
        reasons.append("배당 하락 감지")
    if sharp >= 25:
        reasons.append("Sharp Money 신호")
    if steam >= 10:
        reasons.append("Steam Move")
    if clv >= 14:
        reasons.append("CLV 기대")
    if value_gap >= 8:
        reasons.append("시장 평균 대비 가치")
    if ev >= 5:
        reasons.append("EV 우수")
    elif ev > 0:
        reasons.append("EV 양호")
    if ai_edge >= 5:
        reasons.append("AI Edge 우수")
    if risk == "low":
        reasons.append("위험도 낮음")
    if confidence >= 85:
        reasons.append("AI 신뢰도 높음")

    return reasons or ["관찰 필요"]

def ai_analysis_text(p):
    decision = p.get("decision")
    if decision == "BET":
        return (
            f"{p['pick']}은 시장 암시확률 {p['market_probability']}% 대비 "
            f"AI 예상승률 {p['ai_probability']}%로 Edge {p['ai_edge']}%입니다. "
            f"EV {p['ev']}%, Kelly {p['kelly']}%로 조건이 좋습니다."
        )
    if decision == "WATCH":
        return (
            f"{p['pick']}은 조건은 나쁘지 않지만 강한 확신은 부족합니다. "
            f"AI Edge {p['ai_edge']}%, EV {p['ev']}%라 관찰이 적절합니다."
        )
    return (
        f"{p['pick']}은 현재 No Bet입니다. "
        f"AI Edge {p['ai_edge']}%, EV {p['ev']}%, 위험도 {p['risk']} 기준에서 추천 근거가 부족합니다."
    )

def analyze_market(game, market):
    odds = safe_float(market.get("odds"))
    open_odds = safe_float(market.get("open_odds"))
    pinnacle_odds = safe_float(market.get("pinnacle_odds"))
    market_avg = safe_float(market.get("market_avg"))

    d = drop_rate(open_odds, odds)

    base = 38
    sharp = sharp_component(open_odds, odds, pinnacle_odds, market_avg, market)
    steam = steam_component(open_odds, odds)
    clv = clv_component(odds, pinnacle_odds, market_avg)
    value_gap = value_gap_component(odds, market_avg)
    reverse = reverse_line_component(open_odds, odds, market_avg)

    raw_score = base + sharp + steam + clv + value_gap + reverse
    score = int(max(0, min(99, round(raw_score))))

    ai_prob = round(realistic_probability(score) * 100, 2)
    market_prob = implied_probability(odds)
    ai_edge = round(ai_prob - market_prob, 2)

    ev = ev_percent(score, odds)
    kelly = kelly_percent(score, odds)
    risk = risk_level(score, ev, kelly, d, ai_edge)
    confidence = confidence_score(score, ev, kelly, risk, ai_edge)
    decision = recommendation_decision(confidence, ev, kelly, ai_edge, risk)

    item = {
        "sport": game.get("sport"), "league": game.get("league"),
        "game": f"{game.get('league')} {game.get('home')} vs {game.get('away')}",
        "home": game.get("home"), "away": game.get("away"),
        "starts_at": game.get("starts_at"), "start_in_minutes": game.get("start_in_minutes"),
        "type": market.get("type"), "pick": market.get("pick"),
        "bookmaker": market.get("bookmaker"), "is_pinnacle": market.get("is_pinnacle", False),
        "odds": odds, "open_odds": open_odds, "pinnacle_odds": pinnacle_odds,
        "sharp_odds": pinnacle_odds, "market_avg": market_avg, "domestic_odds": market_avg,
        "best_odds": market.get("best_odds"), "drop_rate": d,
        "implied_probability": market_prob, "market_probability": market_prob,
        "ai_probability": ai_prob, "ai_edge": ai_edge,
        "score": score, "confidence": confidence, "ev": ev, "kelly": kelly,
        "sharp_score": sharp, "steam_score": steam, "clv_score": clv,
        "rlm_score": reverse, "value_score": value_gap,
        "risk": risk, "decision": decision, "grade": recommendation_grade(confidence, decision),
        "bookmakers": market.get("bookmakers", []),
    }

    item["reasons"] = reasons_for_pick(market, d, ev, sharp, steam, clv, value_gap, risk, confidence, ai_edge, decision)
    item["ai_analysis"] = ai_analysis_text(item)
    return item
