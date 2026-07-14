const grid = document.getElementById('grid');
const detail = document.getElementById('detail');
const detailBody = document.getElementById('detail-body');
const search = document.getElementById('search');
const category = document.getElementById('category');

async function api(path, opts) {
  const res = await fetch(path, opts && {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(opts),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

async function loadCatalog() {
  const params = new URLSearchParams();
  if (search.value) params.set('q', search.value);
  if (category.value) params.set('category', category.value);
  const models = await api(`/api/models?${params}`);
  grid.innerHTML = models.map(m => `
    <article class="card" data-id="${m.id}">
      <h3>${m.name} <span class="vendor">${m.vendor}</span></h3>
      <p>${m.description}</p>
      <div class="badges">
        <span class="badge karma">★ Karma ${m.karma}</span>
        <span class="badge green-${m.green.grade}">🌿 Green ${m.green.grade}</span>
        <span class="badge">${m.pricing_mode.replace('_', ' ')} · $${m.base_price_usd}</span>
        <span class="badge">${m.category}</span>
      </div>
    </article>`).join('');
}

grid.addEventListener('click', async (e) => {
  const card = e.target.closest('.card');
  if (card) openDetail(card.dataset.id);
});

async function openDetail(id) {
  const m = await api(`/api/models/${id}`);
  const chain = m.lineage.map(a => a.name).reverse().join(' → ');
  detailBody.innerHTML = `
    <h2>${m.name}</h2>
    <span class="vendor">${m.vendor} · ★ ${m.karma} · SLA ≥ ${m.sla_min_quality * 100}% quality</span>
    <p>${m.description}</p>

    <section>
      <h4>🧬 Model DNA</h4>
      <div class="lineage">${chain}</div>
    </section>

    <section>
      <h4>🌿 Carbon transparency</h4>
      <div>Grade <b>${m.green.grade}</b> · ${m.green.energy_wh_per_1k_tokens} Wh / 1K tokens
        · ${m.green.co2_g_per_1k_tokens} g CO₂ / 1K tokens</div>
    </section>

    <section>
      <h4>🧪 Sandbox (${m.sandbox_trials_left} free trials left)</h4>
      <div class="row">
        <input id="sb-prompt" placeholder="Try a prompt…" style="flex:1">
        <button class="primary" id="sb-run">Run</button>
      </div>
      <div class="result" id="sb-out" hidden></div>
    </section>

    <section>
      <h4>🤝 Negotiate price (agent-to-agent)</h4>
      <div class="row">
        <input id="ng-price" type="number" step="0.001" min="0.001"
               placeholder="Your offer $" style="flex:1">
        <input id="ng-vol" type="number" min="1" value="10000"
               placeholder="Monthly volume" style="flex:1">
        <button class="primary" id="ng-send">Send offer</button>
      </div>
      <div class="result" id="ng-out" hidden></div>
    </section>`;

  detailBody.querySelector('#sb-run').onclick = async () => {
    const out = detailBody.querySelector('#sb-out');
    out.hidden = false;
    try {
      const r = await api('/api/sandbox', {
        model_id: id, prompt: detailBody.querySelector('#sb-prompt').value || 'Hello',
      });
      out.textContent = `${r.output}\n(${r.trials_left} trials left)`;
    } catch (err) { out.textContent = `⚠ ${err.message}`; }
  };

  detailBody.querySelector('#ng-send').onclick = async () => {
    const out = detailBody.querySelector('#ng-out');
    out.hidden = false;
    try {
      const r = await api('/api/negotiate', {
        model_id: id,
        offered_price_usd: parseFloat(detailBody.querySelector('#ng-price').value),
        volume: parseInt(detailBody.querySelector('#ng-vol').value, 10) || 1,
      });
      out.textContent = `${r.status.toUpperCase()} — ${r.seller_message}`;
    } catch (err) { out.textContent = `⚠ ${err.message}`; }
  };

  detail.showModal();
}

search.addEventListener('input', () => loadCatalog());
category.addEventListener('change', () => loadCatalog());
loadCatalog();
