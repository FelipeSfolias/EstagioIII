(function () {
  'use strict';

  /* ── Ícones SVG por categoria ── */
  var CAT_ICONS = {
    notebook:   '<path d="M2 20h20"/><path d="M4 8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10H4z"/>',
    desktop:    '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>',
    monitor:    '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>',
    nobreak:    '<rect x="1" y="6" width="16" height="12" rx="2"/><path d="M23 11v2M6 10v4M10 10v4"/>',
    smartphone: '<rect x="5" y="2" width="14" height="20" rx="2"/><circle cx="12" cy="17" r="1" fill="currentColor"/>',
    servidor:   '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><circle cx="7" cy="6" r="1" fill="currentColor"/><circle cx="7" cy="18" r="1" fill="currentColor"/>',
    impressora: '<path d="M6 9H3a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h3"/><path d="M18 9h3a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-3"/><path d="M6 9V2h12v7"/><rect x="6" y="14" width="12" height="8" rx="1"/>',
    switch:     '<path d="M6 3v12"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
    outro:      '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>',
  };

  /* ── Cores por estado ── */
  var ESTADO = {
    em_uso:     { bg: '#16a34a', tagBg: '#f0fdf4', tagInk: '#166534', label: 'Em Uso' },
    estoque:    { bg: '#2563eb', tagBg: '#eff6ff', tagInk: '#1d4ed8', label: 'Estoque' },
    manutencao: { bg: '#ea580c', tagBg: '#fff7ed', tagInk: '#9a3412', label: 'Manutenção' },
    descartado: { bg: '#475569', tagBg: '#f1f5f9', tagInk: '#334155', label: 'Descartado' },
  };

  function makeSvg(paths, size) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"'
      + ' width="' + size + '" height="' + size + '">' + paths + '</svg>';
  }

  /* ── Referências DOM ── */
  var avatarEl  = document.getElementById('at-avatar');
  var titleEl   = document.getElementById('at-title');
  var estadoTag = document.getElementById('at-estado-tag');
  var catSel    = document.getElementById('id_categoria');
  var estadoSel = document.getElementById('id_estado');
  var patInp    = document.getElementById('id_patrimonio');
  var modInp    = document.getElementById('id_modelo');
  var formEl    = document.getElementById('at-form');

  /* ── Título do card ── */
  function updateTitle() {
    if (!titleEl) return;
    var pat = patInp ? patInp.value.trim() : '';
    var mod = modInp ? modInp.value.trim() : '';
    if (pat && mod)   titleEl.textContent = pat + ' — ' + mod;
    else if (pat)     titleEl.textContent = pat;
    else if (mod)     titleEl.textContent = mod;
    else              titleEl.textContent = 'Novo ativo';
  }

  /* ── Ícone do avatar (por categoria) ── */
  function updateIcon() {
    if (!avatarEl || !catSel) return;
    var key  = catSel.value.toLowerCase();
    var icon = CAT_ICONS[key] || CAT_ICONS.outro;
    avatarEl.innerHTML = makeSvg(icon, 22);
  }

  /* ── Cor do avatar e tag de estado ── */
  function updateEstado() {
    if (!estadoSel) return;
    var cfg = ESTADO[estadoSel.value]
      || { bg: '#94a3b8', tagBg: '#f1f5f9', tagInk: '#64748b', label: estadoSel.options[estadoSel.selectedIndex] ? estadoSel.options[estadoSel.selectedIndex].text : '—' };
    if (avatarEl)  avatarEl.style.background = cfg.bg;
    if (estadoTag) {
      estadoTag.textContent      = cfg.label;
      estadoTag.style.background = cfg.tagBg;
      estadoTag.style.color      = cfg.tagInk;
    }
  }

  /* ── Sugestão de próximo patrimônio ── */
  var URL_PROX = formEl ? (formEl.dataset.urlProximo || '') : '';

  function suggestPatrimonio() {
    if (!patInp || !catSel || !URL_PROX) return;
    if (patInp.value.trim()) return;
    var cat = catSel.value;
    if (!cat) return;
    fetch(URL_PROX + '?categoria=' + encodeURIComponent(cat))
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d.patrimonio && !patInp.value.trim()) patInp.value = d.patrimonio; })
      .catch(function () {});
  }

  /* ── Listeners ── */
  if (catSel) {
    catSel.addEventListener('change', function () {
      updateIcon();
      suggestPatrimonio();
    });
  }
  if (estadoSel) estadoSel.addEventListener('change', updateEstado);
  if (patInp) {
    patInp.addEventListener('input', function () {
      var pos = this.selectionStart;
      this.value = this.value.toUpperCase();
      this.setSelectionRange(pos, pos);
      updateTitle();
    });
  }
  if (modInp) modInp.addEventListener('input', updateTitle);

  /* ── Estado inicial (importante na tela de edição) ── */
  updateIcon();
  updateEstado();
  updateTitle();

  /* ── Avatares pequenos na tabela (ícone + cor por estado) ── */
  document.querySelectorAll('.at-avatar-sm[data-cat]').forEach(function (el) {
    var cat    = (el.dataset.cat    || '').toLowerCase();
    var estado = el.dataset.estado  || '';
    var icon   = CAT_ICONS[cat] || CAT_ICONS.outro;
    var color  = (ESTADO[estado] || { bg: '#94a3b8' }).bg;
    el.innerHTML    = makeSvg(icon, 14);
    el.style.background = color;
  });

  /* ── Mini-avatares de custodiante ── */
  var COLORS = ['#2563eb','#7c3aed','#db2777','#ea580c','#16a34a','#0891b2','#d97706'];

  function avatarColor(name) {
    var hash = 0;
    for (var i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) & 0x7fffffff;
    return COLORS[hash % COLORS.length];
  }

  function initials(name) {
    var parts = name.trim().split(/\s+/);
    return parts.length === 1
      ? parts[0][0].toUpperCase()
      : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  document.querySelectorAll('.at-cust-avatar[data-custname]').forEach(function (el) {
    var name = el.dataset.custname || '';
    el.textContent      = name ? initials(name) : '?';
    el.style.background = name ? avatarColor(name) : '#94a3b8';
  });

  /* ── Autocomplete de Custodiante ── */
  var URL_FUNC  = formEl ? (formEl.dataset.urlCustodiante || '') : '';
  var nomeInp   = document.getElementById('id_custodiante_nome');
  var hidInp    = document.getElementById('id_custodiante_id');
  var listbox   = document.getElementById('at-cust-listbox');

  if (nomeInp && hidInp && listbox && URL_FUNC) {
    var acTimer   = null;
    var acItems   = [];
    var acIdx     = -1;

    function acDebounce(fn, ms) {
      return function () {
        clearTimeout(acTimer);
        acTimer = setTimeout(fn, ms);
      };
    }

    function acShowDropdown(results) {
      acItems = results;
      acIdx   = -1;
      listbox.innerHTML = '';
      if (!results.length) { acHide(); return; }
      results.forEach(function (f, i) {
        var li  = document.createElement('li');
        li.setAttribute('role', 'option');
        li.setAttribute('aria-selected', 'false');
        li.className = 'at-cust-option';
        var av  = document.createElement('div');
        av.className = 'at-cust-avatar';
        av.textContent = initials(f.nome);
        av.style.background = avatarColor(f.nome);
        var txt = document.createElement('div');
        var n   = document.createElement('div');
        n.className = 'at-cust-name';
        n.textContent = f.nome;
        var s   = document.createElement('div');
        s.className = 'at-cust-sub';
        s.textContent = f.setor || f.email || '';
        txt.appendChild(n);
        txt.appendChild(s);
        li.appendChild(av);
        li.appendChild(txt);
        li.addEventListener('mousedown', function (e) {
          e.preventDefault();
          acSelect(i);
        });
        listbox.appendChild(li);
      });
      listbox.hidden = false;
      nomeInp.setAttribute('aria-expanded', 'true');
    }

    function acHide() {
      listbox.hidden = true;
      nomeInp.setAttribute('aria-expanded', 'false');
      acIdx = -1;
    }

    function acSetActive(idx) {
      var opts = listbox.querySelectorAll('[role="option"]');
      opts.forEach(function (o, i) {
        o.classList.toggle('at-cust-active', i === idx);
        o.setAttribute('aria-selected', i === idx ? 'true' : 'false');
      });
      acIdx = idx;
    }

    function acSelect(idx) {
      var f = acItems[idx];
      if (!f) return;
      nomeInp.value = f.nome;
      hidInp.value  = f.id;
      acHide();
    }

    var acFetch = acDebounce(function () {
      var q = nomeInp.value.trim();
      if (!q) { acHide(); hidInp.value = ''; return; }
      fetch(URL_FUNC + '?q=' + encodeURIComponent(q))
        .then(function (r) { return r.json(); })
        .then(function (d) { acShowDropdown(d.results || []); })
        .catch(function () { acHide(); });
    }, 250);

    nomeInp.addEventListener('input', function () {
      if (hidInp.value) hidInp.value = '';
      acFetch();
    });

    nomeInp.addEventListener('keydown', function (e) {
      var opts = listbox.querySelectorAll('[role="option"]');
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        acSetActive(Math.min(acIdx + 1, opts.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        acSetActive(Math.max(acIdx - 1, 0));
      } else if (e.key === 'Enter' && acIdx >= 0) {
        e.preventDefault();
        acSelect(acIdx);
      } else if (e.key === 'Escape') {
        acHide();
      }
    });

    nomeInp.addEventListener('blur', function () {
      setTimeout(acHide, 160);
    });

    nomeInp.addEventListener('change', function () {
      if (!nomeInp.value.trim()) hidInp.value = '';
    });
  }

})();
