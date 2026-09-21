// static/app.js — Frontend: calls Flask backend APIs

const COLORS = ['#38bdf8','#818cf8','#34d399','#fbbf24','#f87171','#a78bfa','#fb923c','#4ade80'];
let portfolioData = { holdings: [], total_value: 0, total_cost: 0, pnl: 0, pnl_pct: 0, count: 0, risk: "—" };
let typingCounter = 0;

// ── Portfolio API calls ───────────────────────────────────────────────

async function addPreset(sym, amt, price) {
  document.getElementById('coinSymbol').value = sym;
  document.getElementById('coinAmount').value = amt;
  document.getElementById('coinPrice').value  = price;
  await addCoin();
}

async function addCoin() {
  const symbol    = document.getElementById('coinSymbol').value.trim().toUpperCase();
  const amount    = parseFloat(document.getElementById('coinAmount').value);
  const buy_price = parseFloat(document.getElementById('coinPrice').value);

  if (!symbol || isNaN(amount) || amount <= 0 || isNaN(buy_price) || buy_price <= 0) {
    flashInputs(); return;
  }

  try {
    const res = await fetch('/api/portfolio/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, amount, buy_price })
    });
    const data = await res.json();
    if (data.error) { alert(data.error); return; }

    portfolioData = data.portfolio;
    document.getElementById('coinSymbol').value = '';
    document.getElementById('coinAmount').value = '';
    document.getElementById('coinPrice').value  = '';
    renderPortfolio();
  } catch (e) {
    alert('Server error: ' + e.message);
  }
}

async function removeCoin(symbol) {
  try {
    const res  = await fetch(`/api/portfolio/remove/${symbol}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.error) { alert(data.error); return; }
    portfolioData = data.portfolio;
    renderPortfolio();
  } catch (e) {
    alert('Server error: ' + e.message);
  }
}

// ── Render Portfolio ──────────────────────────────────────────────────

function renderPortfolio() {
  const container = document.getElementById('assetsContainer');
  const statsRow  = document.getElementById('statsRow');
  const donutArea = document.getElementById('donutArea');
  const d = portfolioData;

  if (!d.holdings || d.holdings.length === 0) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><div>Add your crypto holdings above</div><div style="font-size:10px;color:var(--muted)">or click a quick-add button</div></div>`;
    statsRow.style.display  = 'none';
    donutArea.style.display = 'none';
    document.getElementById('totalValue').textContent  = '$0.00';
    document.getElementById('totalChange').textContent = '—';
    document.getElementById('totalChange').className   = 'portfolio-change';
    return;
  }

  // Header numbers
  document.getElementById('totalValue').textContent =
    '$' + d.total_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const sign     = d.pnl >= 0 ? '+' : '';
  const changeEl = document.getElementById('totalChange');
  changeEl.textContent = `${sign}$${Math.abs(d.pnl).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})} (${sign}${d.pnl_pct.toFixed(2)}%)`;
  changeEl.className   = 'portfolio-change ' + (d.pnl >= 0 ? 'up' : 'down');

  // Stats
  statsRow.style.display = 'flex';
  document.getElementById('holdingCount').textContent = d.count;

  const best   = d.holdings.reduce((b, c) => c.pnl_pct > b.pnl_pct ? c : b);
  document.getElementById('bestAsset').textContent = best.symbol;

  const riskEl = document.getElementById('riskScore');
  riskEl.textContent  = d.risk;
  riskEl.style.color  = d.risk === 'HIGH' ? 'var(--red)' : d.risk === 'MEDIUM' ? 'var(--amber)' : 'var(--green)';

  // Asset cards
  let html = '<div class="assets-grid">';
  d.holdings.forEach((c, i) => {
    const color   = COLORS[i % COLORS.length];
    const badgeBg = c.pnl_pct >= 0 ? 'rgba(52,211,153,0.12)' : 'rgba(248,113,113,0.12)';
    const sign    = c.pnl_pct >= 0 ? '+' : '';
    html += `
      <div class="asset-card" style="border-left:3px solid ${color}">
        <div class="asset-row">
          <span class="asset-symbol">${c.symbol}</span>
          <span class="asset-badge ${c.pnl_pct >= 0 ? 'up' : 'down'}" style="background:${badgeBg}">
            ${sign}${c.pnl_pct.toFixed(1)}%
          </span>
          <button class="del-btn" onclick="removeCoin('${c.symbol}')">✕</button>
        </div>
        <div class="asset-name">${c.amount.toLocaleString()} units · $${c.current_price.toLocaleString()}/unit</div>
        <div class="asset-value" style="color:${color}">
          $${c.value.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})}
        </div>
        <div class="asset-meta">
          ${c.allocation}% of portfolio · Avg $${c.buy_price.toFixed(2)}
        </div>
        <div class="allocation-bar" style="width:${Math.min(c.allocation,100).toFixed(1)}%"></div>
      </div>`;
  });
  html += '</div>';
  container.innerHTML = html;

  renderDonut();
  donutArea.style.display = 'block';
}

function renderDonut() {
  const d      = portfolioData;
  const svg    = document.getElementById('donutSvg');
  const legend = document.getElementById('donutLegend');
  const cx = 55, cy = 55, r = 40, sw = 13;
  const circ   = 2 * Math.PI * r;
  let offset   = 0, paths = '';

  d.holdings.forEach((c, i) => {
    const color = COLORS[i % COLORS.length];
    const pct   = c.allocation / 100;
    const dash  = pct * circ;
    paths += `
      <circle cx="${cx}" cy="${cy}" r="${r}"
        fill="none" stroke="${color}" stroke-width="${sw}"
        stroke-dasharray="${dash.toFixed(2)} ${(circ-dash).toFixed(2)}"
        stroke-dashoffset="${(-offset).toFixed(2)}"
        transform="rotate(-90 ${cx} ${cy})" />`;
    offset += dash;
  });

  svg.innerHTML = `
    <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="${sw}"/>
    ${paths}
    <text x="${cx}" y="${cy+4}" text-anchor="middle" fill="#e2e8f0"
      font-size="9" font-family="Space Mono,monospace">${d.count} COINS</text>`;

  legend.innerHTML = d.holdings.map((c, i) => `
    <div class="legend-row">
      <div class="legend-dot" style="background:${COLORS[i % COLORS.length]}"></div>
      <span class="legend-name">${c.symbol}</span>
      <span class="legend-pct">${c.allocation}%</span>
    </div>`).join('');
}

// ── Chat ─────────────────────────────────────────────────────────────

async function sendMessage() {
  const input   = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');
  const text    = input.value.trim();
  if (!text) return;

  appendMsg('user', text);
  input.value        = '';
  input.style.height = 'auto';
  sendBtn.disabled   = true;

  const typingId = showTyping();

  try {
    const res  = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    removeTyping(typingId);

    if (data.reply === 'OFF_TOPIC') {
      appendOffTopic();
    } else {
      appendMsg('ai', data.reply);
    }
  } catch (e) {
    removeTyping(typingId);
    appendMsg('ai', '⚠️ Server error. Make sure Flask is running on port 5000.');
  }

  sendBtn.disabled = false;
}

function sendQuick(text) {
  document.getElementById('chatInput').value = text;
  sendMessage();
}

function appendMsg(role, text) {
  const msgs    = document.getElementById('messages');
  const div     = document.createElement('div');
  div.className = 'msg ' + role;
  const formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
  div.innerHTML = `
    <div class="msg-label">${role === 'user' ? 'YOU' : 'AI ADVISOR'}</div>
    <div class="msg-bubble">${formatted}</div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function appendOffTopic() {
  const msgs = document.getElementById('messages');
  const div  = document.createElement('div');
  div.className = 'msg ai';
  div.innerHTML = `
    <div class="msg-label">AI ADVISOR</div>
    <div class="off-topic-msg">
      🚫 <strong>Off-topic detected.</strong><br>
      I only handle cryptocurrency questions — holdings, market analysis,
      DCA strategies, risk assessment, or blockchain fundamentals.
    </div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function showTyping() {
  const id   = 'typing-' + (++typingCounter);
  const msgs = document.getElementById('messages');
  const div  = document.createElement('div');
  div.className = 'msg ai'; div.id = id;
  div.innerHTML = `
    <div class="msg-label">AI ADVISOR</div>
    <div class="typing-indicator">
      <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    </div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function flashInputs() {
  document.querySelectorAll('.coin-input').forEach(i => {
    i.style.borderColor = 'var(--red)';
    setTimeout(() => i.style.borderColor = '', 700);
  });
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 90) + 'px';
}