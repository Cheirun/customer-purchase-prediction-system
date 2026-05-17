// app.js  |  Individual Prediction Page
// Auto-fetches a random customer from the dataset on page load
// and re-fetches whenever "Next Customer" is clicked.
// Manual editing of the form still works — hitting "Predict" re-runs manually.

const API = 'http://localhost:5000/api';

// ─────────────────────────────────────────
//  TAB SWITCHING
// ─────────────────────────────────────────
document.querySelectorAll('.pill[data-tab]').forEach(btn => {
  btn.addEventListener('click', () => {
    const id = btn.dataset.tab;
    document.querySelectorAll('.pill[data-tab]').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${id}`).classList.add('active');
    if (id === 'metrics') loadMetrics();
    if (id === 'charts')  loadCharts();
  });
});

// ─────────────────────────────────────────
//  DISCOUNT TOGGLE
// ─────────────────────────────────────────
const discountBox = document.getElementById('f-discount');
const discountLbl = document.getElementById('sw-label');
discountBox.addEventListener('change', () => {
  discountLbl.textContent = discountBox.checked ? 'Yes' : 'No';
});

// ─────────────────────────────────────────
//  AUTO-FETCH ON PAGE LOAD
// ─────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  fetchRandomCustomer();   // load first customer automatically
});

document.getElementById('nextCustomerBtn').addEventListener('click', () => {
  fetchRandomCustomer();
});

async function fetchRandomCustomer() {
  const nextBtn = document.getElementById('nextCustomerBtn');
  nextBtn.disabled = true;
  nextBtn.textContent = '⟳  Loading…';

  // show loading state in results
  showResultsLoading();

  try {
    const res  = await fetch(`${API}/random-customer`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // fill form fields with fetched data
    fillForm(data.customer);

    // show actual label badge if available
    if (data.actual !== null && data.actual !== undefined) {
      showActualLabel(data.actual);
    }

    // render predictions immediately — no need to click predict
    renderResults(data.predictions);

  } catch (err) {
    showErr(err.message);
  } finally {
    nextBtn.disabled = false;
    nextBtn.textContent = '↻  Next Customer';
  }
}

function fillForm(c) {
  document.getElementById('f-age').value    = c.age;
  document.getElementById('f-income').value = c.annual_income;
  document.getElementById('f-time').value   = c.mins_on_site;
  document.getElementById('f-pages').value  = c.pages_viewed;
  document.getElementById('f-orders').value = c.prev_purchases;

  document.getElementById('f-gender').value = c.gender;
  document.getElementById('f-device').value = c.device;

  const shouldCheck = c.discount_given === 1;
  discountBox.checked      = shouldCheck;
  discountLbl.textContent  = shouldCheck ? 'Yes' : 'No';

  // flash animation on the form to show it changed
  const formEl = document.querySelector('.form-pane');
  formEl.classList.remove('flash');
  void formEl.offsetWidth;
  formEl.classList.add('flash');
}

function showActualLabel(actual) {
  const box = document.getElementById('actual-label-box');
  const txt = document.getElementById('actual-label-text');
  box.classList.remove('hidden', 'actual-buy', 'actual-nobuy');
  if (actual === 1) {
    box.classList.add('actual-buy');
    txt.textContent = '✓  Actually Purchased (from dataset)';
  } else {
    box.classList.add('actual-nobuy');
    txt.textContent = '✗  Did NOT Purchase (from dataset)';
  }
  box.classList.remove('hidden');
}

// ─────────────────────────────────────────
//  MANUAL PREDICT (if user edits form)
// ─────────────────────────────────────────
document.getElementById('runBtn').addEventListener('click', handleManualPredict);

async function handleManualPredict() {
  const btn = document.getElementById('runBtn');
  const body = {
    age           : parseFloat(document.getElementById('f-age').value)    || 30,
    annual_income : parseFloat(document.getElementById('f-income').value) || 50000,
    mins_on_site  : parseFloat(document.getElementById('f-time').value)   || 10,
    pages_viewed  : parseFloat(document.getElementById('f-pages').value)  || 5,
    prev_purchases: parseFloat(document.getElementById('f-orders').value) || 2,
    discount_given: discountBox.checked ? 1 : 0,
    gender        : document.getElementById('f-gender').value,
    device        : document.getElementById('f-device').value,
  };

  btn.classList.add('busy');
  btn.querySelector('.run-arrow').textContent = '…';

  // hide actual label since this is a manual / custom input
  document.getElementById('actual-label-box').classList.add('hidden');

  try {
    const res  = await fetch(`${API}/predict`, {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderResults(data.results);
  } catch (err) {
    showErr(err.message);
  } finally {
    btn.classList.remove('busy');
    btn.querySelector('.run-arrow').textContent = '→';
  }
}

// ─────────────────────────────────────────
//  RENDER RESULTS
// ─────────────────────────────────────────
function showResultsLoading() {
  document.getElementById('results-empty').classList.add('hidden');
  document.getElementById('results-cards').classList.add('hidden');
  document.getElementById('verdict').classList.add('hidden');
  document.getElementById('actual-label-box').classList.add('hidden');

  const loadEl = document.getElementById('results-loading');
  loadEl.classList.remove('hidden');
}

function renderResults(results) {
  document.getElementById('results-loading').classList.add('hidden');
  document.getElementById('results-empty').classList.add('hidden');

  const cards   = document.getElementById('results-cards');
  const verdict = document.getElementById('verdict');
  cards.classList.remove('hidden');
  verdict.classList.remove('hidden');
  cards.innerHTML = '';

  let totalProb = 0, buyVotes = 0, count = 0;

  Object.entries(results).forEach(([model, r], i) => {
    const isBuy = r.prediction === 1;
    const prob  = r.probability ?? (isBuy ? 0.7 : 0.3);
    const pct   = Math.round(prob * 100);

    if (isBuy) buyVotes++;
    totalProb += prob;
    count++;

    const card = document.createElement('div');
    card.className = `rc ${isBuy ? 'buy' : 'nobuy'}`;
    card.style.animationDelay = `${i * 55}ms`;
    card.innerHTML = `
      <div class="rc-model">${model}</div>
      <div class="rc-label">${r.label}</div>
      <div class="prob-row">
        <span>Purchase probability</span>
        <span>${pct}%</span>
      </div>
      <div class="prob-track">
        <div class="prob-fill" style="width:0" data-w="${pct}%"></div>
      </div>
    `;
    cards.appendChild(card);
  });

  setTimeout(() => {
    cards.querySelectorAll('.prob-fill').forEach(el => {
      el.style.width = el.dataset.w;
    });
  }, 80);

  const majority  = buyVotes > count / 2;
  const avgPct    = Math.round((totalProb / count) * 100);
  verdict.className = `verdict ${majority ? 'buy' : 'nobuy'}`;
  document.getElementById('verdict-text').textContent =
    majority ? '✓  Likely to Purchase' : '✗  Unlikely to Purchase';
  document.getElementById('verdict-meta').textContent =
    `${buyVotes}/${count} models predict buy  ·  avg probability ${avgPct}%`;
}

// ─────────────────────────────────────────
//  METRICS TABLE
// ─────────────────────────────────────────
let _metricsLoaded = false;
async function loadMetrics() {
  if (_metricsLoaded) return;
  const area = document.getElementById('metrics-area');
  area.innerHTML = '<p class="muted-msg">Fetching scores…</p>';
  try {
    const res  = await fetch(`${API}/scores`);
    const data = await res.json();
    const rows = data.scores;
    if (!rows || !rows.length) {
      area.innerHTML = '<p class="muted-msg">No scores yet.</p>'; return;
    }
    const cols   = ['Accuracy','Precision','Recall','F1','ROC_AUC'];
    const labels = { ROC_AUC: 'ROC AUC' };
    let html = `<table class="metrics-tbl"><thead><tr><th>Model</th>
      ${cols.map(c => `<th>${labels[c]||c}</th>`).join('')}</tr></thead><tbody>`;
    rows.forEach(row => {
      html += `<tr><td>${row.Model}</td>`;
      cols.forEach(c => {
        const v = row[c];
        if (v == null){ html += '<td>—</td>'; return; }
        const n   = parseFloat(v);
        const cls = n >= 0.85 ? 'chip-hi' : n >= 0.70 ? 'chip-mid' : 'chip-lo';
        html += `<td><span class="chip ${cls}">${n.toFixed(4)}</span></td>`;
      });
      html += '</tr>';
    });
    html += '</tbody></table>';
    area.innerHTML = html;
    _metricsLoaded = true;
  } catch(e) {
    area.innerHTML = `<p class="muted-msg">Could not load: ${e.message}</p>`;
  }
}

// ─────────────────────────────────────────
//  CHARTS
// ─────────────────────────────────────────
let _chartsLoaded = false;
async function loadCharts() {
  if (_chartsLoaded) return;
  const area = document.getElementById('charts-area');
  area.innerHTML = '<p class="muted-msg">Fetching charts…</p>';
  try {
    const res  = await fetch(`${API}/charts`);
    const data = await res.json();
    if (!data.charts.length) {
      area.innerHTML = '<p class="muted-msg">No charts generated yet.</p>'; return;
    }
    area.innerHTML = '';
    data.charts.forEach((fname, i) => {
      const label = fname.replace(/^\d+_/,'').replace('.png','').replace(/_/g,' ')
                        .replace(/\b\w/g, c => c.toUpperCase());
      const card = document.createElement('div');
      card.className = 'chart-card';
      card.style.animationDelay = `${i * 45}ms`;
      card.innerHTML = `
        <img src="http://localhost:5000/charts/${fname}" alt="${label}" loading="lazy"/>
        <div class="chart-caption">${label}</div>
      `;
      area.appendChild(card);
    });
    _chartsLoaded = true;
  } catch(e) {
    area.innerHTML = `<p class="muted-msg">Error: ${e.message}</p>`;
  }
}

// ─────────────────────────────────────────
//  ERROR
// ─────────────────────────────────────────
function showErr(msg) {
  document.getElementById('results-loading').classList.add('hidden');
  const empty = document.getElementById('results-empty');
  document.getElementById('results-cards').classList.add('hidden');
  document.getElementById('verdict').classList.add('hidden');
  empty.classList.remove('hidden');
  empty.innerHTML = `
    <div class="empty-circle" style="border-color:#fca5a5"></div>
    <p style="color:#b91c1c">Error: ${msg}</p>
    <p style="font-size:.8rem;color:var(--ink-40)">Make sure Flask is running on port 5000.</p>
  `;
}
