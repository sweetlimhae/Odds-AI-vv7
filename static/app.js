const sportEl = document.getElementById("sport");
const minutesEl = document.getElementById("minutes");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");

document.getElementById("gamesBtn").addEventListener("click", loadGames);
document.getElementById("analyzeBtn").addEventListener("click", analyze);

function params() {
  return `sport=${encodeURIComponent(sportEl.value)}&minutes=${encodeURIComponent(minutesEl.value)}`;
}

function setStatus(text) {
  statusEl.innerHTML = text ? `<div class="notice">${text}</div>` : "";
}

function decisionFromMarket(m) {
  const odds = Number(m.odds || 0);
  const openOdds = Number(m.open_odds || 0);
  const avg = Number(m.market_avg || 0);

  const dropRate = openOdds > 0 ? ((openOdds - odds) / openOdds) * 100 : 0;
  const edge = avg > 0 ? ((avg - odds) / odds) * 100 : 0;

  if (dropRate >= 5 && edge >= 2) return "BET";
  if (dropRate >= 2 || edge >= 1) return "WATCH";
  return "NO BET";
}

function decisionClass(decision) {
  if (decision === "BET") return "bet";
  if (decision === "WATCH") return "watch";
  return "nobet";
}

function renderGames(games) {
  if (!games || games.length === 0) {
    resultsEl.innerHTML = `<div class="card">조건에 맞는 경기가 없습니다.</div>`;
    return;
  }

  resultsEl.innerHTML = games.map(game => {
    const market = (game.markets || [])[0] || {};
    const decision = decisionFromMarket(market);

    const odds = Number(market.odds || 0);
    const openOdds = Number(market.open_odds || 0);
    const avg = Number(market.market_avg || 0);
    const pinnacle = Number(market.pinnacle_odds || 0);

    const dropRate = openOdds > 0 ? (((openOdds - odds) / openOdds) * 100).toFixed(1) : "-";
    const edge = avg > 0 ? (((avg - odds) / odds) * 100).toFixed(1) : "-";
    const ev = pinnacle > 0 ? (((pinnacle / odds - 1) * 100).toFixed(1)) : edge;

    return `
      <article class="card game-card ${decisionClass(decision)}">
        <div class="card-top">
          <div class="tag">${game.sport || "-"} · ${game.league || "-"}</div>
          <div class="decision ${decisionClass(decision)}">${decision}</div>
        </div>

        <h2>${game.home || "-"} vs ${game.away || "-"}</h2>
        <p class="muted">시작까지 ${game.start_in_minutes ?? "-"}분</p>

        <div class="pick-box">
          <small>추천픽</small>
          <b>${market.pick || "-"}</b>
        </div>

        <div class="summary-grid">
          <div><small>현재배당</small><b>${market.odds ?? "-"}</b></div>
          <div><small>초기배당</small><b>${market.open_odds ?? "-"}</b></div>
          <div><small>Pinnacle</small><b>${market.pinnacle_odds ?? "-"}</b></div>
          <div><small>시장평균</small><b>${market.market_avg ?? "-"}</b></div>
          <div><small>하락률</small><b>${dropRate}%</b></div>
          <div><small>Edge</small><b>${edge}%</b></div>
          <div><small>EV</small><b>${ev}%</b></div>
          <div><small>북메이커</small><b>${market.bookmaker || "-"}</b></div>
        </div>
      </article>
    `;
  }).join("");
}

async function loadGames() {
  setStatus("경기 불러오는 중...");
  resultsEl.innerHTML = `<div class="card">불러오는 중...</div>`;

  try {
    const res = await fetch(`/api/live-games?${params()}`);
    const data = await res.json();
    setStatus(data.notice || `총 ${data.count || 0}경기`);
    renderGames(data.games);
  } catch (err) {
    console.error(err);
    resultsEl.innerHTML = `<div class="card danger">경기 불러오기 실패</div>`;
  }
}

async function analyze() {
  setStatus("AI 분석 중...");
  resultsEl.innerHTML = `<div class="card">AI 분석 중...</div>`;

  try {
    const res = await fetch(`/api/recommendations?${params()}`);
    const data = await res.json();

    setStatus(data.notice || "AI 분석 완료");

    resultsEl.innerHTML = `
      <article class="card highlight">
        <h2>오늘 분석 요약</h2>
        <p>분석픽: ${data.summary?.total_picks ?? 0}</p>
        <p>BET: ${data.summary?.bet_count ?? 0}</p>
        <p>관찰: ${data.summary?.watch_count ?? 0}</p>
        <p>No Bet: ${data.summary?.no_bet_count ?? 0}</p>
      </article>
      ${(data.top_picks || []).map((p, i) => `
        <article class="card">
          <div class="tag">${p.decision || "-"}</div>
          <h2>${p.game || "-"}</h2>
          <p><b>추천: ${p.pick || "-"}</b></p>
          <p>신뢰도: ${p.confidence ?? p.score ?? 0}%</p>
          <p>EV: ${p.ev ?? "-"}%</p>
          <p>Edge: ${p.ai_edge ?? "-"}%</p>
        </article>
      `).join("")}
    `;
  } catch (err) {
    console.error(err);
    resultsEl.innerHTML = `<div class="card danger">AI 분석 실패</div>`;
  }
}

loadGames();
