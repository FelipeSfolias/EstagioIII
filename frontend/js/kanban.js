(function () {
  'use strict';

  const CSRF = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';

  function post(url, data) {
    const fd = new FormData();
    Object.entries(data).forEach(([k, v]) => fd.append(k, v));
    fd.append('csrfmiddlewaretoken', CSRF);
    return fetch(url, { method: 'POST', body: fd });
  }

  function postJSON(url, data) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
      body: JSON.stringify(data),
    });
  }

  // ── Board: arrastar colunas ──────────────────────────────────────
  const board = document.getElementById('kb-board');

  Sortable.create(board, {
    animation: 180,
    handle: '.kb-col-header',
    filter: '.kb-col-menu, .kb-col-color-btn, .kb-col-del-btn, .kb-col-title',
    preventOnFilter: false,
    draggable: '.kb-col',
    ghostClass: 'kb-col-ghost',
    chosenClass: 'kb-col-chosen',
    onEnd() {
      const order = [...board.querySelectorAll('.kb-col')].map(el => el.dataset.chave);
      postJSON('/projetos/colunas/reordenar/', { order });
    },
  });

  // ── Colunas: arrastar cards ──────────────────────────────────────
  function initColSort(colBody) {
    Sortable.create(colBody, {
      group: 'cards',
      animation: 150,
      ghostClass: 'kcard-ghost',
      chosenClass: 'kcard-chosen',
      dragClass: 'kcard-drag',
      onEnd(evt) {
        const card = evt.item;
        const toCol = evt.to.dataset.chave;
        if (!toCol) return;
        card.dataset.coluna = toCol;
        const cardId = card.dataset.id;
        post(`/projetos/card/${cardId}/mover/`, { coluna_key: toCol });

        updateColCount(evt.from.closest('.kb-col'));
        updateColCount(evt.to.closest('.kb-col'));
      },
    });
  }

  document.querySelectorAll('.kb-col-body').forEach(initColSort);

  function updateColCount(col) {
    if (!col) return;
    const count = col.querySelectorAll('.kcard').length;
    const badge = col.querySelector('.kb-col-badge');
    if (badge) badge.textContent = count;
  }

  // ── Renomear coluna (contenteditable) ───────────────────────────
  document.querySelectorAll('.kb-col-title').forEach(el => {
    el.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); el.blur(); } });
    el.addEventListener('blur', () => {
      const newTitle = el.textContent.trim();
      const colId = el.dataset.colId;
      if (!newTitle || newTitle === el.dataset.original) return;
      el.dataset.original = newTitle;
      post(`/projetos/coluna/${colId}/editar/`, { titulo: newTitle });
    });
  });

  // ── Color picker ─────────────────────────────────────────────────
  const picker = document.getElementById('kb-color-picker');
  let pickerTargetId = null;

  document.querySelectorAll('.kb-col-color-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      pickerTargetId = btn.dataset.colId;
      const rect = btn.getBoundingClientRect();
      picker.style.top = (rect.bottom + 6 + window.scrollY) + 'px';
      picker.style.left = rect.left + 'px';
      picker.style.display = 'block';
    });
  });

  document.querySelectorAll('.kb-cp-swatch').forEach(sw => {
    sw.addEventListener('click', () => {
      if (!pickerTargetId) return;
      const cor = sw.dataset.cor;
      picker.style.display = 'none';
      // --col-cor agora fica na .kb-col (não no header)
      const col = board.querySelector(`.kb-col[data-id="${pickerTargetId}"]`);
      if (col) col.style.setProperty('--col-cor', cor);
      post(`/projetos/coluna/${pickerTargetId}/editar/`, { cor });
      pickerTargetId = null;
    });
  });

  document.addEventListener('click', e => {
    if (!picker.contains(e.target) && !e.target.closest('.kb-col-color-btn')) {
      picker.style.display = 'none';
    }
  });

  // ── Excluir coluna ──────────────────────────────────────────────
  function wireDelBtn(btn) {
    let pending = false;
    let timer = null;
    btn.addEventListener('click', e => {
      e.stopPropagation();
      if (!pending) {
        pending = true;
        btn.title = 'Clique novamente para confirmar';
        btn.style.cssText = 'background:#fee2e2;color:#dc2626;border-radius:6px;';
        timer = setTimeout(() => {
          pending = false;
          btn.title = 'Excluir coluna';
          btn.style.cssText = '';
        }, 2500);
        return;
      }
      clearTimeout(timer);
      pending = false;
      btn.style.cssText = '';
      const colId = btn.dataset.colId;
      const col = board.querySelector(`.kb-col[data-id="${colId}"]`);
      post(`/projetos/coluna/${colId}/excluir/`, {}).then(r => r.json()).then(d => {
        if (d.ok && col) col.remove();
      });
    });
  }
  document.querySelectorAll('.kb-col-del-btn').forEach(wireDelBtn);

  // ── Adicionar coluna (modal) ──────────────────────────────────────
  const colBackdrop = document.getElementById('kmodal-col-backdrop');
  const kmcNome = document.getElementById('kmc-nome');

  function openColModal() {
    kmcNome.value = '';
    document.querySelectorAll('.kmc-cor').forEach((b, i) => b.classList.toggle('is-active', i === 0));
    colBackdrop.classList.add('is-open');
    document.body.classList.add('no-scroll');
    setTimeout(() => kmcNome.focus(), 60);
  }
  function closeColModal() {
    colBackdrop.classList.remove('is-open');
    document.body.classList.remove('no-scroll');
  }

  document.getElementById('kb-add-col-btn').addEventListener('click', openColModal);
  document.getElementById('kmc-close').addEventListener('click', closeColModal);
  document.getElementById('kmc-cancel').addEventListener('click', closeColModal);
  colBackdrop.addEventListener('click', e => { if (e.target === colBackdrop) closeColModal(); });
  kmcNome.addEventListener('keydown', e => { if (e.key === 'Enter') document.getElementById('kmc-save').click(); });

  document.querySelectorAll('.kmc-cor').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.kmc-cor').forEach(b => b.classList.remove('is-active'));
      btn.classList.add('is-active');
    });
  });

  document.getElementById('kmc-save').addEventListener('click', () => {
    const titulo = kmcNome.value.trim();
    if (!titulo) { kmcNome.focus(); return; }
    const activeCor = document.querySelector('.kmc-cor.is-active');
    const cor = activeCor ? activeCor.dataset.cor : '#94a3b8';
    post('/projetos/coluna/criar/', { titulo, cor })
      .then(r => {
        if (!r.ok) throw new Error(`Erro ${r.status}`);
        return r.json();
      })
      .then(d => {
        if (!d.ok) throw new Error('Falha ao criar coluna');
        closeColModal();
        const addWrap = document.querySelector('.kb-add-col-wrap');
        const colEl = buildColEl(d);
        board.insertBefore(colEl, addWrap);
        initColSort(colEl.querySelector('.kb-col-body'));
        wireColEvents(colEl);
      })
      .catch(err => {
        console.error('Erro ao criar coluna:', err);
        if (typeof GModal !== 'undefined') {
          GModal.alert('Erro ao salvar', 'Não foi possível criar a coluna. Tente novamente.');
        }
      });
  });

  function buildColEl(d) {
    const col = document.createElement('div');
    col.className = 'kb-col';
    col.dataset.chave = d.chave;
    col.dataset.id = d.id;
    // --col-cor fica na .kb-col (não no header)
    col.style.setProperty('--col-cor', d.cor);
    col.innerHTML = `
      <div class="kb-col-header">
        <div class="kb-col-title-row">
          <span class="kb-col-badge">0</span>
          <span class="kb-col-title" contenteditable="true" data-original="${d.titulo}" data-col-id="${d.id}">${d.titulo}</span>
          <div class="kb-col-menu">
            <button class="kb-col-color-btn" data-col-id="${d.id}" title="Cor da coluna">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/></svg>
            </button>
            <button class="kb-col-del-btn" data-col-id="${d.id}" data-col-chave="${d.chave}" title="Excluir coluna">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
        </div>
      </div>
      <div class="kb-col-body" data-chave="${d.chave}">
        <div class="kb-col-empty">Sem cards nesta coluna</div>
      </div>
      <div class="kb-col-footer">
        <button class="kb-col-add-card-btn" data-chave="${d.chave}">
          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M5 12h14"/></svg>
          Adicionar card
        </button>
      </div>`;
    return col;
  }

  function wireColEvents(col) {
    const titleEl = col.querySelector('.kb-col-title');
    if (titleEl) {
      titleEl.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); titleEl.blur(); } });
      titleEl.addEventListener('blur', () => {
        const newTitle = titleEl.textContent.trim();
        const colId = titleEl.dataset.colId;
        if (!newTitle || newTitle === titleEl.dataset.original) return;
        titleEl.dataset.original = newTitle;
        post(`/projetos/coluna/${colId}/editar/`, { titulo: newTitle });
      });
    }
    const colorBtn = col.querySelector('.kb-col-color-btn');
    if (colorBtn) {
      colorBtn.addEventListener('click', e => {
        e.stopPropagation();
        pickerTargetId = colorBtn.dataset.colId;
        const rect = colorBtn.getBoundingClientRect();
        picker.style.top = (rect.bottom + 6 + window.scrollY) + 'px';
        picker.style.left = rect.left + 'px';
        picker.style.display = 'block';
      });
    }
    const delBtn = col.querySelector('.kb-col-del-btn');
    if (delBtn) wireDelBtn(delBtn);
  }

  // ── Modal de card ────────────────────────────────────────────────
  const KCOLORS = { blue: '#3b82f6', green: '#10b981', purple: '#8b5cf6', orange: '#f97316', gray: '#94a3b8', default: '#e2e8f0' };
  const cardExtras = new Map();

  function getExtras(id) {
    if (!cardExtras.has(String(id))) cardExtras.set(String(id), { desc: '', checklist: [] });
    return cardExtras.get(String(id));
  }

  let currentCard = null;
  let kmodalMode = 'edit';
  let kmodalColChave = '';
  const backdrop = document.getElementById('kmodal-backdrop');

  function setAccentBar(color) {
    const bar = document.getElementById('km-accent-bar');
    if (bar) bar.style.background = KCOLORS[color] || KCOLORS.default;
  }

  function escHtml(s) {
    return String(s || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function pctClass(pct) {
    pct = parseFloat(pct) || 0;
    if (pct >= 100) return 'pct-done';
    if (pct > 0) return 'pct-progress';
    return '';
  }

  function renderChecklist(items) {
    const list = document.getElementById('km-cl-list');
    list.innerHTML = '';
    items.forEach((item, i) => {
      const li = document.createElement('li');
      li.className = 'kmodal-cl-item';
      li.innerHTML = `
        <label class="kmodal-cl-label">
          <input type="checkbox" class="kmodal-cl-cb" data-idx="${i}" ${item.done ? 'checked' : ''}>
          <span class="kmodal-cl-text${item.done ? ' is-done' : ''}">${escHtml(item.text)}</span>
        </label>
        <button type="button" class="kmodal-cl-del" data-idx="${i}" title="Remover">
          <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>`;
      list.appendChild(li);
    });
    syncClProgress(items);
  }

  function syncClProgress(items) {
    const total = items.length;
    const done = items.filter(i => i.done).length;
    const pct = total ? Math.round(done / total * 100) : 0;
    document.getElementById('km-cl-pct').textContent = `${pct}%`;
    document.getElementById('km-cl-bar').style.width = `${pct}%`;
    const hint = document.getElementById('km-progress-hint');
    const pInput = document.getElementById('km-progress');
    if (total > 0) {
      hint.style.display = 'block';
      pInput.value = pct;
      pInput.disabled = true;
    } else {
      hint.style.display = 'none';
      pInput.disabled = false;
    }
  }

  document.getElementById('km-cl-list').addEventListener('change', e => {
    if (!e.target.classList.contains('kmodal-cl-cb')) return;
    const extras = currentCard ? getExtras(currentCard.dataset.id) : null;
    if (!extras) return;
    const idx = parseInt(e.target.dataset.idx);
    extras.checklist[idx].done = e.target.checked;
    const span = e.target.nextElementSibling;
    span.classList.toggle('is-done', e.target.checked);
    syncClProgress(extras.checklist);
  });

  document.getElementById('km-cl-list').addEventListener('click', e => {
    const btn = e.target.closest('.kmodal-cl-del');
    if (!btn) return;
    const extras = currentCard ? getExtras(currentCard.dataset.id) : null;
    if (!extras) return;
    extras.checklist.splice(parseInt(btn.dataset.idx), 1);
    renderChecklist(extras.checklist);
  });

  function addClItem() {
    const inp = document.getElementById('km-cl-input');
    const text = inp.value.trim();
    if (!text) { inp.focus(); return; }
    const id = currentCard ? currentCard.dataset.id : `tmp_${Date.now()}`;
    const extras = getExtras(id);
    if (!currentCard) kmodalColChave && (currentCard = { dataset: { id } });
    extras.checklist.push({ text, done: false });
    renderChecklist(extras.checklist);
    inp.value = '';
    inp.focus();
  }
  document.getElementById('km-cl-add-btn').addEventListener('click', addClItem);
  document.getElementById('km-cl-input').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); addClItem(); } });

  function openCardModal(mode, card, colChave) {
    kmodalMode = mode;
    currentCard = card;
    kmodalColChave = colChave || '';
    const extras = card ? getExtras(card.dataset.id) : { desc: '', checklist: [] };
    document.getElementById('km-title').value    = card ? (card.dataset.title    || '') : '';
    document.getElementById('km-people').value   = card ? (card.dataset.resp     || '') : '';
    document.getElementById('km-area').value     = card ? (card.dataset.area     || '') : '';
    document.getElementById('km-date').value     = card ? (card.dataset.prazo    || '') : '';
    document.getElementById('km-progress').value = card ? (card.dataset.progress || '0') : '0';
    document.getElementById('km-progress').disabled = false;
    document.getElementById('km-progress-hint').style.display = 'none';
    document.getElementById('km-desc').value     = extras.desc;
    document.getElementById('km-cl-input').value = '';
    const color = card ? (card.dataset.color || 'default') : 'default';
    backdrop.querySelectorAll('.kcolor').forEach(b => b.classList.toggle('is-active', b.dataset.kcolor === color));
    setAccentBar(color);
    renderChecklist(extras.checklist);
    backdrop.classList.add('is-open');
    document.body.classList.add('no-scroll');
    setTimeout(() => document.getElementById('km-title').focus(), 60);
  }

  board.addEventListener('click', e => {
    const addBtn = e.target.closest('.kb-col-add-card-btn');
    if (addBtn) { openCardModal('create', null, addBtn.dataset.chave); return; }
    const card = e.target.closest('.kcard');
    if (!card) return;
    openCardModal('edit', card, '');
  });

  function closeModal() {
    backdrop.classList.remove('is-open');
    document.body.classList.remove('no-scroll');
    currentCard = null;
  }

  document.getElementById('kmodal-close').addEventListener('click', closeModal);
  document.getElementById('kmodal-close2').addEventListener('click', closeModal);
  backdrop.addEventListener('click', e => { if (e.target === backdrop) closeModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeModal(); closeColModal(); } });

  backdrop.addEventListener('click', e => {
    const cb = e.target.closest('.kcolor');
    if (!cb || cb.closest('#kmodal-col-backdrop')) return;
    backdrop.querySelectorAll('.kcolor').forEach(b => b.classList.remove('is-active'));
    cb.classList.add('is-active');
    setAccentBar(cb.dataset.kcolor);
  });

  // ── Constrói HTML de um card novo ───────────────────────────────
  const PRAZO_ICON = `<svg width="11" height="11" viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="1" stroke="currentColor" stroke-width="1.2"/><path d="M5 1V3M11 1V3M2 5H14" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>`;

  function buildCardEl(d) {
    const card = document.createElement('div');
    const colorClass = d.cor && d.cor !== 'default' ? `kcard-color-${d.cor}` : '';
    card.className = `kcard ${colorClass}`.trim();
    card.dataset.id = d.id;
    card.dataset.title = d.titulo;
    card.dataset.resp = d.responsavel || '';
    card.dataset.area = d.area || '';
    card.dataset.progress = d.percentual || 0;
    card.dataset.color = d.cor || 'default';
    card.dataset.prazo = d.prazo || '';
    card.dataset.atrasado = 'false';
    const initial = d.responsavel ? d.responsavel[0].toUpperCase() : '?';
    const pct = parseFloat(d.percentual) || 0;
    const cls = pctClass(pct);
    card.innerHTML = `
      <div class="kcard-header">
        <h4 class="kcard-title">${escHtml(d.titulo)}</h4>
        <span class="kcard-progress-label ${cls}">${pct}%</span>
      </div>
      <div class="kcard-progress-wrap">
        <div class="kcard-progress-bar" style="--k-progress:${pct}%"></div>
      </div>
      <div class="kcard-footer">
        <div class="kcard-avatar">${initial}</div>
        <span class="kcard-meta-sub" data-area="${escHtml(d.area || '')}">${escHtml(d.area || '')}</span>
        <span class="kcard-meta-main" hidden>${escHtml(d.responsavel || '')}</span>
        ${d.prazo ? `<div class="kcard-prazo">${PRAZO_ICON}${escHtml(d.prazo)}</div>` : ''}
      </div>`;
    return card;
  }

  function applyCardProgress(card, pct) {
    pct = parseFloat(pct) || 0;
    card.dataset.progress = pct;
    const lbl = card.querySelector('.kcard-progress-label');
    if (lbl) {
      lbl.textContent = `${pct}%`;
      lbl.className = `kcard-progress-label ${pctClass(pct)}`.trim();
    }
    const bar = card.querySelector('.kcard-progress-bar');
    if (bar) bar.style.setProperty('--k-progress', `${pct}%`);
  }

  document.getElementById('kmodal-save').addEventListener('click', () => {
    const newTitle    = document.getElementById('km-title').value.trim();
    const newPeople   = document.getElementById('km-people').value.trim();
    const newArea     = document.getElementById('km-area').value.trim();
    const newDate     = document.getElementById('km-date').value;
    const newDesc     = document.getElementById('km-desc').value;
    const activeColor = backdrop.querySelector('.kcolor.is-active');
    const color = activeColor ? activeColor.dataset.kcolor : 'default';

    if (kmodalMode === 'create') {
      if (!newTitle) { document.getElementById('km-title').focus(); return; }
      const chave = kmodalColChave;
      const btn = document.getElementById('kmodal-save');
      btn.disabled = true;
      post('/projetos/card/criar/', { coluna_key: chave, titulo: newTitle,
        responsavel: newPeople, area: newArea, prazo: newDate, cor: color })
        .then(r => {
          if (!r.ok) throw new Error(`Erro ${r.status}`);
          return r.json();
        })
        .then(d => {
          if (!d.ok) throw new Error(d.error || 'Falha ao criar card');
          getExtras(d.id).desc = newDesc;
          const colBody = board.querySelector(`.kb-col-body[data-chave="${chave}"]`);
          if (colBody) {
            const empty = colBody.querySelector('.kb-col-empty');
            if (empty) empty.remove();
            colBody.appendChild(buildCardEl(d));
            updateColCount(colBody.closest('.kb-col'));
          }
          closeModal();
        })
        .catch(err => {
          console.error('Erro ao criar card:', err);
          if (typeof GModal !== 'undefined') {
            GModal.alert('Erro ao salvar', 'Não foi possível criar o card. Verifique sua conexão e tente novamente.');
          }
        })
        .finally(() => { btn.disabled = false; });
      return;
    }

    if (!currentCard) return;
    const extras = getExtras(currentCard.dataset.id);
    extras.desc = newDesc;

    let pct = parseFloat(document.getElementById('km-progress').value) || 0;
    if (extras.checklist.length > 0) {
      const done = extras.checklist.filter(i => i.done).length;
      pct = Math.round(done / extras.checklist.length * 100);
    }

    if (newTitle) {
      currentCard.dataset.title = newTitle;
      const titleEl = currentCard.querySelector('.kcard-title');
      if (titleEl) titleEl.textContent = newTitle;
    }
    if (newPeople) {
      currentCard.dataset.resp = newPeople;
      const main = currentCard.querySelector('.kcard-meta-main');
      if (main) main.textContent = newPeople;
      const av = currentCard.querySelector('.kcard-avatar');
      if (av) av.textContent = newPeople[0].toUpperCase();
    }
    if (newArea) {
      currentCard.dataset.area = newArea;
      const sub = currentCard.querySelector('.kcard-meta-sub');
      if (sub) { sub.textContent = newArea; sub.dataset.area = newArea; }
    }

    // Atualiza prazo no footer
    currentCard.dataset.prazo = newDate;
    let prazoEl = currentCard.querySelector('.kcard-prazo');
    if (newDate) {
      if (!prazoEl) {
        prazoEl = document.createElement('div');
        prazoEl.className = 'kcard-prazo';
        currentCard.querySelector('.kcard-footer').appendChild(prazoEl);
      }
      prazoEl.innerHTML = `${PRAZO_ICON}${escHtml(newDate)}`;
    } else if (prazoEl) {
      prazoEl.remove();
    }

    currentCard.dataset.color = color;
    ['blue', 'green', 'purple', 'orange', 'gray'].forEach(c => currentCard.classList.remove('kcard-color-' + c));
    if (color !== 'default') currentCard.classList.add('kcard-color-' + color);
    applyCardProgress(currentCard, pct);

    // Checklist badge
    const footer = currentCard.querySelector('.kcard-footer');
    const existingBadge = footer ? footer.querySelector('.kcard-cl-badge') : null;
    if (extras.checklist.length > 0 && footer) {
      const done = extras.checklist.filter(i => i.done).length;
      const badge = existingBadge || document.createElement('span');
      badge.className = 'kcard-cl-badge';
      badge.textContent = `${done}/${extras.checklist.length}`;
      if (!existingBadge) footer.insertBefore(badge, footer.querySelector('.kcard-prazo'));
    } else if (existingBadge) {
      existingBadge.remove();
    }

    closeModal();
  });

})();
