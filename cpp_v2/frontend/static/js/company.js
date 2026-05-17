// company.js  |  Company Batch Prediction Page
// Auto-fetches predictions from the live dataset — no CSV upload needed.
// Supports pagination, filter (all/buy/nobuy), min-probability search,
// and full CSV download of all 1000 predictions.

const API = 'http://localhost:5000/api';

let currentPage   = 1;
let currentFilter = 'all';
let currentMinProb = 0;
let totalPages    = 1;
const PAGE_SIZE   = 50;

// ─────────────────────────────────────────
//  ON LOAD — fetch immediately
// ─────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  fetchPredictions();
});

// ─────────────────────────────────────────
//  FILTER BUTTONS
// ─────────────────────────────────────────
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    currentPage   = 1;
    fetchPredictions();
  });
});

// ─────────────────────────────────────────
//  MIN PROBABILITY SEARCH
// ─────────────────────────────────────────
const probInput = document.getElementById('prob-filter');
const probVal   = document.getElementById('prob-val');

probInput.addEventListener('input', () => {
  currentMinProb = parseInt(probInput.value) || 0;
  probVal.textContent = currentMinProb + '%';
});
probInput.addEventListener('change', () => {
  currentPage = 1;
  fetchPredictions();
});

// ─────────────────────────────────────────
//  PAGINATION
// ─────────────────────────────────────────
document.getElementById('prevBtn').addEventListener('click', () => {
  if (currentPage > 1) { currentPage--; fetchPredictions(); }
});
document.getElementById('nextBtn').addEventListener('click', () => {
  if (currentPage < totalPages) { currentPage++; fetchPredictions(); }
});

// ─────────────────────────────────────────
//  REFRESH BUTTON
// ─────────────────────────────────────────
document.getElementById('refreshBtn').addEventListener('click', () => {
  currentPage = 1;
  fetchPredictions();
});

// ─────────────────────────────────────────
//  DOWNLOAD ALL PREDICTIONS
// ─────────────────────────────────────────
document.getElementById('downloadAllBtn').addEventListener('click', () => {
  window.location.href = `${API}/auto-predict/download`;
});

// ─────────────────────────────────────────
//  MAIN FETCH FUNCTION
// ─────────────────────────────────────────
async function fetchPredictions() {
  setLoading(true);

  const url = `${API}/auto-predict?n=${PAGE_SIZE}&page=${currentPage}&filter=${currentFilter}&search=${currentMinProb}`;

  try {
    const res  = await fetch(url);
    if (!res.ok) { const e = await res.json(); throw new Error(e.error || res.status); }
    const data = await res.json();

    totalPages = data.total_pages;
    renderSummary(data);
    renderTable(data.rows);
    renderPagination(data.page, data.total_pages, data.total_rows);

  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
}

// ─────────────────────────────────────────
//  RENDER SUMMARY CARDS
// ─────────────────────────────────────────
function renderSummary(data) {
  document.getElementById('sum-buy').textContent    = data.will_buy;
  document.getElementById('sum-nobuy').textContent  = data.wont_buy;
  document.getElementById('sum-showing').textContent = data.rows_shown;
  document.getElementById('sum-prob').textContent   = data.avg_prob + '%';
  document.getElementById('co-summary').classList.remove('hidden');
}

// ─────────────────────────────────────────
//  RENDER TABLE
// ─────────────────────────────────────────
function renderTable(rows) {
  const tbody = document.getElementById('batchBody');
  tbody.innerHTML = '';

  if (!rows || rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;color:var(--ink-40);padding:24px;">
      No records match the current filter.</td></tr>`;
    document.getElementById('co-table-wrap').classList.remove('hidden');
    return;
  }

  const startIdx = (currentPage - 1) * PAGE_SIZE;

  rows.forEach((row, i) => {
    const isBuy = row.prediction === 1;
    const tr    = document.createElement('tr');
    tr.innerHTML = `
      <td>${startIdx + i + 1}</td>
      <td>${row.age ?? '—'}</td>
      <td>${row.annual_income != null ? Number(row.annual_income).toLocaleString('en-IN') : '—'}</td>
      <td>${row.mins_on_site ?? '—'}</td>
      <td>${row.pages_viewed ?? '—'}</td>
      <td>${row.prev_purchases ?? '—'}</td>
      <td>${row.discount_given == 1 ? 'Yes' : 'No'}</td>
      <td>${row.gender ?? '—'}</td>
      <td>${row.device ?? '—'}</td>
      <td>
        <div class="prob-inline">
          <div class="prob-inline-bar" style="width:${row.probability}%"
               class="${isBuy ? 'buy' : 'nobuy'}"></div>
          <span>${row.probability}%</span>
        </div>
      </td>
      <td>
        <span class="verdict-badge ${isBuy ? 'vb-buy' : 'vb-nobuy'}">
          ${row.verdict}
        </span>
      </td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById('co-table-wrap').classList.remove('hidden');
}

// ─────────────────────────────────────────
//  PAGINATION CONTROLS
// ─────────────────────────────────────────
function renderPagination(page, total, totalRows) {
  document.getElementById('page-info').textContent =
    `Page ${page} of ${total}  ·  ${totalRows} total customers`;
  document.getElementById('prevBtn').disabled = page <= 1;
  document.getElementById('nextBtn').disabled = page >= total;
  document.getElementById('pagination-row').classList.remove('hidden');
}

// ─────────────────────────────────────────
//  LOADING STATE
// ─────────────────────────────────────────
function setLoading(on) {
  const overlay = document.getElementById('table-loading');
  overlay.classList.toggle('hidden', !on);
  document.getElementById('refreshBtn').disabled = on;
}

// ─────────────────────────────────────────
//  ERROR
// ─────────────────────────────────────────
function showError(msg) {
  const tbody = document.getElementById('batchBody');
  tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;color:#b91c1c;padding:20px;">
    ⚠ ${msg} — make sure Flask is running on port 5000.</td></tr>`;
  document.getElementById('co-table-wrap').classList.remove('hidden');
}

// ─────────────────────────────────────────
//  RETRAIN
// ─────────────────────────────────────────
document.getElementById('retrainBtn').addEventListener('click', async () => {
  const btn = document.getElementById('retrainBtn');
  const msg = document.getElementById('retrain-msg');

  if (!confirm('Delete saved models and retrain from scratch?\nThis will take a minute.')) return;

  btn.disabled    = true;
  btn.textContent = '⟳  Retraining…';
  msg.className   = 'retrain-msg hidden';

  try {
    const res  = await fetch(`${API}/retrain`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    msg.textContent = '✓  ' + data.message;
    msg.className   = 'retrain-msg ok';
    msg.classList.remove('hidden');
    // refresh the table with new predictions
    currentPage = 1;
    fetchPredictions();
  } catch (err) {
    msg.textContent = '✗  ' + err.message;
    msg.className   = 'retrain-msg err';
    msg.classList.remove('hidden');
  } finally {
    btn.disabled    = false;
    btn.textContent = '⟳  Retrain Now';
  }
});
