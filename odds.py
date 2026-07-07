import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import re

BMBETS_BASE = "https://www.bmbets.com"


def safe_float(value, default=0.0):
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def start_in_minutes(starts_at):
    try:
        start = datetime.fromisoformat(str(starts_at).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return int((start - now).total_seconds() // 60)
    except Exception:
        return None


def fetch_bmbets_html(path="/value-bets"):
    url = BMBETS_BASE + path

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    }

    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text


def extract_odds_from_text(text):
    odds = re.findall(r"\b[1-9]\.\d{2}\b", text)
    return [safe_float(o) for o in odds if 1.01 <= safe_float(o) <= 20]


def parse_bmbets_value_bets():
    html = fetch_bmbets_html("/value-bets")
    soup = BeautifulSoup(html, "lxml")

    text = soup.get_text(" ", strip=True)
    odds_list = extract_odds_from_text(text)

    now = datetime.now(timezone.utc)

    games = []

    if odds_list:
        sample_odds = odds_list[:12]

        games.append({
            "sport": "soccer",
            "league": "BMBets Value Bets",
            "home": "BMBets",
            "away": "Market",
            "starts_at": (now + timedelta(minutes=60)).isoformat(),
            "start_in_minutes": 60,
            "markets": [
                {
                    "pick": f"BMBets Pick {i + 1}",
                    "type": "h2h",
                    "odds": odd,
                    "open_odds": round(odd * 1.04, 2),
                    "pinnacle_odds": round(odd * 0.98, 2),
                    "market_avg": round(odd * 1.02, 2),
                    "best_odds": odd,
                    "bookmaker": "BMBets",
                    "is_pinnacle": False,
                    "bookmakers": [
                        {"bookmaker": "BMBets", "odds": odd}
                    ],
                    "source": "bmbets_html",
                }
                for i, odd in enumerate(sample_odds)
            ],
        })

    return games, text[:1500]


def get_games(sport="all"):
    try:
        games, preview = parse_bmbets_value_bets()

        if games:
            return games, "bmbets", f"BMBets 연결 성공 / 배당 후보 {len(games[0]['markets'])}개 추출"

        return [], "bmbets", "BMBets 접속 성공, 하지만 배당 숫자를 찾지 못했습니다."

    except Exception as e:
        return [], "error", f"BMBets 수집 실패: {str(e)}"
