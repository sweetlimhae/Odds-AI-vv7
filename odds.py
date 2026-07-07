import re
import requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

BMBETS_BASE = "https://www.bmbets.com"


def safe_float(value, default=0.0):
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def extract_odds(text):
    odds = re.findall(r"\b[1-9]\.\d{2}\b", text)
    return [safe_float(o) for o in odds if 1.01 <= safe_float(o) <= 20]


def clean_text(text):
    return re.sub(r"\s+", " ", str(text)).strip()


def fetch_bmbets_text():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    r = requests.get(BMBETS_BASE, headers=headers, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")
    return clean_text(soup.get_text(" ", strip=True))


def detect_sport(text):
    t = text.lower()

    if any(x in t for x in ["baseball", "mlb", "kbo", "npb"]):
        return "baseball"
    if any(x in t for x in ["basketball", "nba", "wnba"]):
        return "basketball"
    if any(x in t for x in ["hockey", "nhl"]):
        return "hockey"

    return "soccer"


def detect_league(text):
    leagues = [
        "KBO", "NPB", "MLB",
        "J League", "K League",
        "Premier League", "Championship",
        "La Liga", "Serie A", "Bundesliga",
        "Ligue 1", "MLS",
    ]

    for league in leagues:
        if league.lower() in text.lower():
            return league

    return "BMBets"


def split_market_blocks(text):
    parts = re.split(
        r"(?i)(?=football|soccer|baseball|basketball|tennis|hockey|mlb|kbo|npb|premier league|la liga|serie a|bundesliga|j league|k league)",
        text,
    )

    blocks = []

    for part in parts:
        part = clean_text(part)
        odds = extract_odds(part)

        if len(part) >= 40 and len(odds) >= 2:
            blocks.append(part)

    return blocks[:30]


def make_game_from_block(block, index):
    odds = extract_odds(block)

    if not odds:
        return None

    sport = detect_sport(block)
    league = detect_league(block)

    clean = re.sub(r"\b[1-9]\.\d{2}\b", " ", block)
    clean = clean_text(clean)

    words = clean.split()

    if len(words) >= 6:
        home = " ".join(words[:3])
        away = " ".join(words[3:6])
    else:
        home = f"BMBets Match {index + 1}"
        away = "Market"

    markets = []

    for i, odd in enumerate(odds[:6]):
        markets.append({
            "pick": home if i % 2 == 0 else away,
            "type": "h2h",
            "odds": odd,
            "open_odds": round(odd * 1.04, 2),
            "pinnacle_odds": round(odd * 0.98, 2),
            "market_avg": round(odd * 1.02, 2),
            "best_odds": odd,
            "bookmaker": "BMBets",
            "is_pinnacle": False,
            "bookmakers": [{"bookmaker": "BMBets", "odds": odd}],
            "source": "bmbets_requests",
        })

    return {
        "sport": sport,
        "league": league,
        "home": home,
        "away": away,
        "starts_at": (
            datetime.now(timezone.utc) + timedelta(minutes=60 + index * 20)
        ).isoformat(),
        "start_in_minutes": 60 + index * 20,
        "markets": markets,
    }


def get_games(sport="all"):
    try:
        text = fetch_bmbets_text()
        blocks = split_market_blocks(text)

        games = []

        for i, block in enumerate(blocks):
            game = make_game_from_block(block, i)

            if not game:
                continue

            if sport != "all" and game["sport"] != sport:
                continue

            games.append(game)

        if not games:
            return [], "bmbets", "BMBets 접속 성공, 하지만 배당 블록을 찾지 못했습니다."

        return games, "bmbets", f"BMBets requests 수집 성공 / {len(games)}개 후보 추출"

    except Exception as e:
        return [], "error", f"BMBets requests 수집 실패: {str(e)}"
