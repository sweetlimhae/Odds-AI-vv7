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

function decisionLabel(decision) {
  if (decision === "BET") return "BET";
  if (decision === "WATCH") return "관찰";
  return "NO BET";
}

function riskLabel(risk) {
  if (risk === "low") return "낮음";
  if (risk === "medium") return "보통";
  if (risk === "high") return "높음";
  return risk || "-";
}

function rankIcon(i) {
  if (i === 0) return "🥇";
  if (i === 1) return "🥈";
  if (i === 2) return "🥉";
  return `#${i + 1}`;
}

function confidenceBar(score) {
  score = Math.max(0, Math.min(100, Number(score || 0)));
  return `<div class="meter"><div class="meter-fill" style="width:${score}%"></div></div><small>AI 신뢰도 ${score}%</small>`;
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
        <div><small>추천조합</small><b>${summary.recommendation_count ?? 0}</b></div>
        <div><small>최고신뢰도</small><b>${summary.top_confidence ?? 0}%</b></div>
        <div><small>평균EV</small><b>${summary.avg_ev ?? 0}%</b></div>
        <div><small>평균Edge</small><b>${summary.avg_edge ?? 0}%</b></div>
      </div>
      <p class="reason">${summary.message || ""}</p>
    </article>`;
}

function renderGames(games) {
  if (!games || games.length === 0) {
    resultsEl.innerHTML = "<div class='card'>조건에 맞는 경기가 없습니다.</div>";
    return;
  }

  resultsEl.innerHTML = games.map(game => `
    <article class="card">
      <div class="tag">${game.sport || ""} · ${game.league || ""}</div>
      <h2>${game.home || "-"} vs ${game.away || "-"}</h2>
      <p>시작까지: ${game.start_in_minutes ?? "-"}분</p>
      <p>시작시간: ${game.starts_at || "-"}</p>
      ${(game.markets || []).map(m => `
        <div class="market">
          <b>${m.pick || "-"}</b>
          <span>현재배당 ${m.odds ?? "-"}</span>
          <span>Pinnacle ${m.pinnacle_odds ?? "-"}</span>
          <span>시장평균 ${m.market_avg ?? "-"}</span>
          <span>북메이커 ${m.bookmaker || "-"}</span>
        </div>`).join("")}
    </article>`).join("");
}

async function loadGames() {
  try {
    setStatus("오늘 경기 불러오는 중...");
    resultsEl.innerHTML = "<div class='card'>불러오는 중...</div>";
    const res = await fetch(`/api/live-games?${params()}`);
    const data = await res.json();
    setStatus(data.notice || `총 ${data.count || 0}경기`);
    renderGames(data.games);
  } catch (err) {
    console.error(err);
    resultsEl.innerHTML = "<div class='card danger'>경기를 불러오지 못했습니다.</div>";
  }
}

function renderPick(p, i) {
  return `
    <div class="pick">
      <div class="rank">${rankIcon(i)} 추천순위 ${i + 1}</div>
      <div class="tag">${decisionLabel(p.decision)} · 위험도 ${riskLabel(p.risk)}</div>
      <h3>${p.game || `${p.home || "-"} vs ${p.away || "-"}`}</h3>
      ${confidenceBar(p.confidence ?? p.score ?? 0)}
      <p><b>추천: ${p.pick || "-"}</b></p>
      <p>등급: <b>${p.grade || "-"}</b></p>
      <div class="summary-grid">
        <div><small>현재배당</small><b>${p.odds ?? "-"}</b></div>
        <div><small>Pinnacle</small><b>${p.pinnacle_odds ?? "-"}</b></div>
        <div><small>시장평균</small><b>${p.market_avg ?? "-"}</b></div>
        <div><small>하락률</small><b>${p.drop_rate ?? "-"}%</b></div>
        <div><small>AI 승률</small><b>${p.ai_probability ?? "-"}%</b></div>
        <div><small>시장확률</small><b>${p.market_probability ?? "-"}%</b></div>
        <div><small>AI Edge</small><b>${p.ai_edge ?? "-"}%</b></div>
        <div><small>EV</small><b>${p.ev ?? "-"}%</b></div>
        <div><small>Kelly</small><b>${p.kelly ?? "-"}%</b></div>
        <div><small>Sharp</small><b>${p.sharp_score ?? "-"}점</b></div>
        <div><small>Steam</small><b>${p.steam_score ?? "-"}점</b></div>
        <div><small>CLV</small><b>${p.clv_score ?? "-"}점</b></div>
      </div>
      <p class="reason">${(p.reasons || []).join(" · ")}</p>
      <p class="reason">AI 분석: ${p.ai_analysis || "-"}</p>
    </div>`;
}

function renderCombos(combos) {
  if (!combos || combos.length === 0) {
    return `<article class="card danger"><h2>No Bet</h2><p>현재 조건에서는 추천 조합이 없습니다. 관망을 추천합니다.</p></article>`;
  }

  return combos.map((combo, comboIndex) => `
    <article class="card highlight">
      <h2>${rankIcon(comboIndex)} ${combo.type || "추천 조합"}</h2>
      <div class="summary-grid">
        <div><small>폴더수</small><b>${combo.folder_size ?? (combo.picks || []).length}</b></div>
        <div><small>총배당</small><b>${combo.total_odds ?? "-"}</b></div>
        <div><small>평균점수</small><b>${combo.avg_score ?? "-"}</b></div>
        <div><small>평균신뢰도</small><b>${combo.avg_confidence ?? "-"}%</b></div>
        <div><small>평균EV</small><b>${combo.avg_ev ?? "-"}%</b></div>
        <div><small>평균Edge</small><b>${combo.avg_edge ?? "-"}%</b></div>
      </div>
      ${(combo.picks || []).map((p, i) => renderPick(p, i)).join("")}
    </article>`).join("");
}

function renderTopPicks(topPicks) {
  if (!topPicks || topPicks.length === 0) return "";
  return `<article class="card"><h2>단일픽 TOP 10</h2>${topPicks.slice(0, 10).map((p, i) => renderPick(p, i)).join("")}</article>`;
}

function renderExcluded(excluded) {
  if (!excluded || excluded.length === 0) return "";
  return `<article class="card danger"><h2>No Bet 제외 경기</h2>${excluded.slice(0, 12).map(g => `<p>${g.game || "-"} / ${g.pick || "-"} / 신뢰도 ${g.confidence ?? "-"} / EV ${g.ev ?? "-"} / Edge ${g.ai_edge ?? "-"}</p>`).join("")}</article>`;
}

async function analyze() {
  try {
    setStatus("AI 분석 중...");
    resultsEl.innerHTML = "<div class='card'>AI 분석 중...</div>";
    const res = await fetch(`/api/recommendations?${params()}`);
    const data = await res.json();
    setStatus(data.notice || "AI 분석 완료");
    resultsEl.innerHTML = renderSummary(data.summary) + renderCombos(data.combos || []) + renderTopPicks(data.top_picks || []) + renderExcluded(data.excluded || []);
  } catch (err) {
    console.error(err);
    resultsEl.innerHTML = "<div class='card danger'>AI 분석 실패</div>";
  }
}
