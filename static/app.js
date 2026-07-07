const sportEl = document.getElementById("sport");
const minutesEl = document.getElementById("minutes");
const resultsEl = document.getElementById("results");
const statusEl = document.getElementById("status");

document.getElementById("gamesBtn").addEventListener("click", loadGames);
document.getElementById("analyzeBtn").addEventListener("click", analyze);

function params() {
  return `sport=${sportEl.value}&minutes=${minutesEl.value}`;
}

function setStatus(text) {
  statusEl.innerHTML = text ? `<div class="notice">${text}</div>` : "";
}

function renderGames(games) {
  if (!games || games.length === 0) {
    resultsEl.innerHTML = `<div class="card">조건에 맞는 경기가 없습니다.</div>`;
    return;
  }

  resultsEl.innerHTML = games.map(game => `
    <article class="card">
      <div class="tag">${game.sport} · ${game.league}</div>
      <h2>${game.home} vs ${game.away}</h2>
      <p>시작까지: ${game.start_in_minutes ?? "-"}분</p>

      ${(game.markets || []).map(m => `
        <div class="market">
          <b>${m.pick}</b>
          <span>현재배당 ${m.odds}</span>
          <span>초기배당 ${m.open_odds}</span>
          <span>Pinnacle ${m.pinnacle_odds}</span>
          <span>시장평균 ${m.market_avg}</span>
        </div>
      `).join("")}
    </article>
  `).join("");
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
    resultsEl.innerHTML = `<div class="card danger">경기 불러오기 실패</div>`;
  }
}

function renderSummary(summary) {
  if (!summary) return "";

  return `
    <article class="card highlight">
      <h2>오늘 분석 요약</h2>
      <div class="summary-grid">
        <div><small>분석픽</small><b>${summary.total_picks ?? 0}</b></div>
        <div><small>BET</small><b>${summary.bet_count ?? 0}</b></div>
        <div><small>관찰</small><b>${summary.watch_count ?? 0}</b></div>
        <div><small>No Bet</small><b>${summary.no_bet_count ?? 0}</b></div>
        <div><small>평균EV</small><b>${summary.avg_ev ?? 0}%</b></div>
        <div><small>평균Edge</small><b>${summary.avg_edge ?? 0}%</b></div>
      </div>
      <p>${summary.message || ""}</p>
    </article>
  `;
}

function renderPick(p, i) {
  return `
    <div class="pick">
      <div class="tag">${p.decision || "NO_BET"}</div>
      <h3>${p.game || "-"}</h3>
      <p><b>추천: ${p.pick || "-"}</b></p>
      <p>신뢰도: ${p.confidence ?? p.score ?? 0}%</p>
      <p>현재배당: ${p.odds ?? "-"}</p>
      <p>Pinnacle: ${p.pinnacle_odds ?? "-"}</p>
      <p>EV: ${p.ev ?? "-"}%</p>
      <p>Edge: ${p.ai_edge ?? "-"}%</p>
      <p class="reason">${(p.reasons || []).join(" · ")}</p>
    </div>
  `;
}

function renderPicks(picks) {
  if (!picks || picks.length === 0) {
    return `<article class="card">추천픽이 없습니다.</article>`;
  }

  return `
    <article class="card">
      <h2>AI 추천픽</h2>
      ${picks.map((p, i) => renderPick(p, i)).join("")}
    </article>
  `;
}

async function analyze() {
  setStatus("AI 분석 중...");
  resultsEl.innerHTML = `<div class="card">AI 분석 중...</div>`;

  try {
    const res = await fetch(`/api/recommendations?${params()}`);
    const data = await res.json();

    setStatus(data.notice || "AI 분석 완료");
    resultsEl.innerHTML =
      renderSummary(data.summary) +
      renderPicks(data.top_picks || []);
  } catch (err) {
    resultsEl.innerHTML = `<div class="card danger">AI 분석 실패</div>`;
  }
}

loadGames();
