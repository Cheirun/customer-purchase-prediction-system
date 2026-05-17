// history.js  |  History & Analytics Page
// reads everything directly from MongoDB Atlas via the Flask API

const API = 'http://localhost:5000/api';
let trendChartInstance = null;

// ─────────────────────────────────────────
//  ON LOAD
// ─────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  checkAtlas();
  loadAccuracy();
  loadHistory();
  loadRetrainHistory();
});

document.getElementById('refreshHistoryBtn').addEventListener('click', () => {
  loadHistory();
});

// ─────────────────────────────────────────
//  ATLAS STATUS BANNER
// ─────────────────────────────────────────
async function checkAtlas() {
  const banner = document.getElementById('atlas-banner');
  const text   = document.getElementById('atlas-status-text');
  banner.classList.remove('hidden');

  try {
    const res  = await fetch(`${API}/health`);
    const data = await res.json();

    if (data.atlas === 'connected') {
      banner.className = 'atlas-banner ok';
      text.textContent = `MongoDB Atlas — Connected  ·  ${data.dataset_rows} records loaded`;
    } else {
      banner.className = 'atlas-banner err';
      text.textContent = 'MongoDB Atlas — Unreachable. Check your MONGO_URI in .env';
    }
  } catch (e) {
    banner.className = 'atlas-banner err';
    text.textContent = `Could not reach Flask server: ${e.message}`;
  }
}

// ─────────────────────────────────────────
//  LIVE ACCURACY
// ─────────────────────────────────────────
async function loadAccuracy() {
  const cardsEl = document.getElementById('accuracy-cards');

  try {
    const res  = await fetch(`${API}/accuracy`);
    const data = await res.json();

    // update hero stats
    const s = data.summary;
    if (s) {
      document.getElementById('h-total').textContent   = s.total || '—';
      document.getElementById('h-buyrate').textContent =
        s.total ? Math.round((s.buy_count / s.total) * 100) + '%' : '—';
      document.getElementById('h-avgprob').textContent = s.avg_prob ? s.avg_prob + '%' : '—';
    }

    // accuracy cards
    const stats = data.stats || [];
    if (stats.length === 0) {
      cardsEl.innerHTML = '<p class="muted-msg" style="grid-column:1/-1">No predictions logged yet — make some predictions first.</p>';
      return;
    }

    cardsEl.innerHTML = '';
    stats.forEach(m => {
      const acc   = m.accuracy !== null ? Math.round(m.accuracy * 100) : null;
      const tier  = acc === null ? 'lo' : acc >= 85 ? 'hi' : acc >= 70 ? 'mid' : 'lo';
      const card  = document.createElement('div');
      card.className = `acc-card ${tier}-card`;
      card.innerHTML = `
        <div class="acc-model">${m.model_name}</div>
        <div class="acc-score ${tier}">${acc !== null ? acc + '%' : 'N/A'}</div>
        <div class="acc-bar-bg">
          <div class="acc-bar-fill" style="width:0" data-w="${acc || 0}%"></div>
        </div>
        <div class="acc-meta">
          ${m.correct_count} / ${m.total} correct
          &nbsp;·&nbsp; avg prob ${Math.round((m.avg_probability || 0) * 100)}%
        </div>
      `;
      cardsEl.appendChild(card);
    });

    // animate bars
    setTimeout(() => {
      cardsEl.querySelectorAll('.acc-bar-fill').forEach(el => {
        el.style.width = el.dataset.w;
      });
    }, 100);

    // draw trend chart
    drawTrendChart(data.daily || []);

  } catch (e) {
    cardsEl.innerHTML = `<p class="muted-msg" style="grid-column:1/-1">Could not load accuracy: ${e.message}</p>`;
  }
}

// ─────────────────────────────────────────
//  TREND CHART
// ─────────────────────────────────────────
function drawTrendChart(daily) {
  const canvas  = document.getElementById('trendChart');
  const emptyEl = document.getElementById('trend-empty');

  if (!daily || daily.length === 0) {
    canvas.classList.add('hidden');
    emptyEl.classList.remove('hidden');
    return;
  }

  const labels   = daily.map(d => d._id);
  const totals   = daily.map(d => d.total);
  const buys     = daily.map(d => d.buy_count);
  const nobuys   = daily.map(d => d.total - d.buy_count);

  if (trendChartInstance) trendChartInstance.destroy();

  trendChartInstance = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label          : 'Will Buy',
          data           : buys,
          backgroundColor: 'rgba(45,106,79,.75)',
          borderRadius   : 4,
        },
        {
          label          : "Won't Buy",
          data           : nobuys,
          backgroundColor: 'rgba(185,28,28,.55)',
          borderRadius   : 4,
        },
      ],
    },
    options: {
      responsive      : true,
      plugins         : { legend: { position: 'top' } },
      scales          : {
        x: { stacked: true, grid: { display: false } },
        y: { stacked: true, beginAtZero: true, ticks: { stepSize: 1 } },
      },
    },
  });
}

// ─────────────────────────────────────────
//  RETRAIN HISTORY
// ─────────────────────────────────────────
async function loadRetrainHistory() {
  const area = document.getElementById('retrain-history-area');
  try {
    const res  = await fetch(`${API}/retrain-history`);
    const data = await res.json();
    const rows = data.history || [];

    if (rows.length === 0) {
      area.innerHTML = '<p class="muted-msg">No retrain events logged yet.</p>';
      return;
    }

    let html = `
      <table class="retrain-tbl">
        <thead>
          <tr>
            <th>#</th><th>Date & Time</th><th>Accuracy</th>
            <th>F1 Score</th><th>ROC AUC</th><th>Rows Used</th><th>Notes</th>
          </tr>
        </thead>
        <tbody>
    `;
    rows.forEach((r, i) => {
      html += `<tr>
        <td>${i + 1}</td>
        <td>${r.retrained_at}</td>
        <td><span class="chip ${chipClass(r.accuracy)}">${(r.accuracy*100).toFixed(1)}%</span></td>
        <td><span class="chip ${chipClass(r.f1_score)}">${(r.f1_score*100).toFixed(1)}%</span></td>
        <td><span class="chip ${chipClass(r.roc_auc)}">${(r.roc_auc*100).toFixed(1)}%</span></td>
        <td>${r.rows_used}</td>
        <td>${r.notes || '—'}</td>
      </tr>`;
    });
    html += '</tbody></table>';
    area.innerHTML = html;

  } catch (e) {
    area.innerHTML = `<p class="muted-msg">Could not load retrain history: ${e.message}</p>`;
  }
}

// ─────────────────────────────────────────
//  PREDICTION HISTORY TABLE
// ─────────────────────────────────────────
async function loadHistory() {
  const loading = document.getElementById('hist-loading');
  const tbody   = document.getElementById('histBody');

  loading.classList.remove('hidden');
  tbody.innerHTML = '';

  try {
    const res  = await fetch(`${API}/history?limit=100`);
    const data = await res.json();
    const rows = data.history || [];

    loading.classList.add('hidden');

    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--ink-40);padding:20px;">
        No predictions logged yet.</td></tr>`;
      return;
    }

    rows.forEach((r, i) => {
      const isBuy   = r.prediction === 1;
      const correct = r.correct;
      const correctHtml =
        correct === 1 ? '<span class="chip chip-hi">✓ Yes</span>' :
        correct === 0 ? '<span class="chip chip-lo">✗ No</span>'  :
                        '<span style="color:var(--ink-40)">—</span>';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${i + 1}</td>
        <td style="font-family:var(--sans);font-weight:600">${r.model_name}</td>
        <td>
          <span class="verdict-badge ${isBuy ? 'vb-buy' : 'vb-nobuy'}">
            ${isBuy ? 'Will Buy' : "Won't Buy"}
          </span>
        </td>
        <td>${Math.round((r.probability || 0) * 100)}%</td>
        <td>${correctHtml}</td>
        <td style="color:var(--ink-40)">${r.predicted_at || '—'}</td>
      `;
      tbody.appendChild(tr);
    });

  } catch (e) {
    loading.classList.add('hidden');
    tbody.innerHTML = `<tr><td colspan="6" style="color:#b91c1c;padding:16px;">
      Error: ${e.message}</td></tr>`;
  }
}

// ─────────────────────────────────────────
//  HELPERS
// ─────────────────────────────────────────
function chipClass(val) {
  if (val == null) return 'chip-lo';
  const n = parseFloat(val);
  return n >= 0.85 ? 'chip-hi' : n >= 0.70 ? 'chip-mid' : 'chip-lo';
}
