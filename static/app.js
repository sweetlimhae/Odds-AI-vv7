function decisionFromMarket(m) {
  const odds = Number(m.odds || 0);
  const openOdds = Number(m.open_odds || 0);
  const pinnacle = Number(m.pinnacle_odds || 0);
  const avg = Number(m.market_avg || 0);

  const dropRate = openOdds > 0 ? ((openOdds - odds) / openOdds) * 100 : 0;
  const edge = avg > 0 ? ((avg - odds) / odds) * 100 : 0;
  const ev = pinnacle > 0 ? ((pinnacle / odds - 1) * 100) : edge;

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
