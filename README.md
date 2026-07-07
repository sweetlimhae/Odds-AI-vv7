# Odds AI V5

Render 무료 서버에서 실행 가능한 안정형 구조입니다.

## 배포 순서

1. GitHub 저장소에 모든 파일 업로드
2. Render Build Command:
   pip install -r requirements.txt
3. Render Start Command:
   gunicorn app:app
4. Environment:
   ODDS_API_KEY=The Odds API Key

## 주요 기능

- Odds API 실시간 배당
- 경기 시작 10~180분 필터
- Pinnacle 우선 분석
- 시장 평균 배당 비교
- AI 예상승률
- 시장 암시확률
- AI Edge
- EV
- Kelly
- BET / WATCH / NO_BET 판단

Playwright는 Render Free 메모리 문제로 제외했습니다.
