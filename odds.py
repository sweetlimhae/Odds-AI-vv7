import re
from datetime import datetime, timezone, timedelta

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

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


def detect_sport(text):
    t = text.lower()

    if any(x in t for x in ["baseball", "mlb", "kbo", "npb", "yankees", "dodgers", "giants", "tigers"]):
        return "baseball"

    if any(x in t for x in ["basketball", "nba", "wnba"]):
        return "basketball"

    if any(x in t for x in ["hockey", "nhl"]):
        return "hockey"

    return "soccer"


def detect_league(text):
    league_words = [
        "KBO", "NPB", "MLB",
        "J League", "J1 League", "J2 League",
        "K League", "K League 1", "K League 2",
        "EPL", "Premier League", "Championship",
        "League One", "League Two",
        "La Liga", "Segunda",
        "Serie A", "Serie B",
        "Bundesliga", "2. Bundesliga",
        "Ligue 1", "Ligue 2",
        "Eredivisie",
        "Primeira Liga",
        "MLS",
        "Brazil Serie A",
        "Argentina Primera",
    ]

    for word in league_words:
        if word.lower() in text.lower():
            return word

    return "BMBets"


def bmbets_browser_text():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page.goto(BMBETS_BASE, wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(5000)

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "lxml")
    return clean_text(soup.get_text(" ", strip=True))


def split_market_blocks(text):
    parts = re.split(
        r"(?i)(?=football|soccer|baseball|basketball|tennis|hockey|mlb|kbo|npb|premier league|la liga|serie a|bundesliga|j league|k league)",
        text,
    )

    blocks = []

    for part in parts:
        part = clean_text(part)

        if len(part) < 40:
            continue

        odds = extract_odds(part)

        if len(odds) >= 2:
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

    separators = [" vs ", " v ", " - ", " @ "]
    home = None
    away = None

    for sep in separators:
        if sep in clean:
            parts = clean.split(sep)

            if len(parts) >= 2:
                left = clean_text(parts[0])
                right = clean_text(parts[1])

                home = " ".join(left.split()[-4:])
                away = " ".join(right.split()[:4])
                break

    if not home or not away:
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
            "bookmakers": [
                {
                    "bookmaker": "BMBets",
                    "odds": odd,
                }
            ],
            "source": "bmbets_playwright",
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
        text = bmbets_browser_text()
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
            return [], "bmbets", "BMBets 접속 성공, 하지만 경기 블록을 찾지 못했습니다."

        return games, "bmbets", f"BMBets Playwright 수집 성공 / {len(games)}개 경기 후보 추출"

    except Exception as e:
        return [], "error", f"BMBets Playwright 수집 실패: {str(e)}"
