import os

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
MIN_START_MINUTES = int(os.getenv("MIN_START_MINUTES", "10"))
MAX_START_MINUTES = int(os.getenv("MAX_START_MINUTES", "180"))

SUPPORTED_SPORTS = {
    "soccer": [
        ("soccer", "soccer_epl"),
        ("soccer", "soccer_spain_la_liga"),
        ("soccer", "soccer_italy_serie_a"),
        ("soccer", "soccer_germany_bundesliga"),
        ("soccer", "soccer_france_ligue_one"),
    ],
    "baseball": [
        ("baseball", "baseball_mlb"),
    ],
}
