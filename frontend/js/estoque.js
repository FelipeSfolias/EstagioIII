(function () {
  'use strict';

  var STATUS = {
    ok:           { bg: '#16a34a', tagBg: '#f0fdf4', tagInk: '#166534', label: 'Em estoque' },
    abaixo_minimo:{ bg: '#ea580c', tagBg: '#fff7ed', tagInk: '#9a3412', label: 'Abaixo do mínimo' },
    esgotado:     { bg: '#dc2626', tagBg: '#fef2f2', tagInk: '#991b1b', label: 'Esgotado' },
  };

  var BOX_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"'
    + ' width="14" height="14">'
    + '<path d="M3 7l9-4 9 4-9 4-9-4z"/>'
    + '<path d="M3 7v10l9 4 9-4V7"/>'
    + '<path d="M12 11v10"/>'
    + '</svg>';

  function calcStatus(qtde, minimo) {
    qtde   = parseInt(qtde)   || 0;
    minimo = parseInt(minimo) || 0;
    if (qtde <= 0)       return 'esgotado';
    if (qtde < minimo)   return 'abaixo_minimo';
    return 'ok';
  }

  /* ── Referências do form ── */
  var avatarEl   = document.getElementById('es-avatar');
  var titleEl    = document.getElementById('es-title');
  var statusTag  = document.getElementById('es-status-tag');
  var skuInp     = document.getElementById('id_sku');
  var nomeInp    = document.getElementById('id_nome');
  var qtdeInp    = document.getElementById('id_qtde');
  var minInp     = document.getElementById('id_nivel_minimo');
  var unidadeInp = document.getElementById('id_unidade');

  /* ── Atualizar header do card ── */
  function updateFormHeader() {
    var qtde   = parseInt(qtdeInp ? qtdeInp.value : '0') || 0;
    var min    = parseInt(minInp  ? minInp.value  : '0') || 0;
    var status = calcStatus(qtde, min);
    var cfg    = STATUS[status] || STATUS.ok;

    if (avatarEl)  avatarEl.style.background  = cfg.bg;
    if (statusTag) {
      statusTag.textContent      = cfg.label;
      statusTag.style.background = cfg.tagBg;
      statusTag.style.color      = cfg.tagInk;
    }
    if (titleEl && nomeInp) {
      titleEl.textContent = nomeInp.value.trim() || 'Novo item';
    }
  }

  /* ── Sufixo de unidade nos campos numéricos ── */
  function updateUnitSuffix() {
    var unit = (unidadeInp ? unidadeInp.value.trim() : '') || '';
    document.querySelectorAll('.es-unit-suffix').forEach(function (el) {
      el.textContent = unit || '—';
    });
  }

  /* ── SKU auto-maiúsculo ── */
  if (skuInp) {
    skuInp.addEventListener('input', function () {
      var pos = this.selectionStart;
      this.value = this.value.toUpperCase();
      this.setSelectionRange(pos, pos);
    });
  }

  if (nomeInp)    nomeInp.addEventListener('input', updateFormHeader);
  if (qtdeInp)    qtdeInp.addEventListener('input', updateFormHeader);
  if (minInp)     minInp.addEventListener('input', updateFormHeader);
  if (unidadeInp) unidadeInp.addEventListener('input', updateUnitSuffix);

  /* ── Estado inicial (edit page pré-preenchida) ── */
  updateFormHeader();
  updateUnitSuffix();

  /* ── Avatares na tabela ── */
  document.querySelectorAll('.es-avatar-sm[data-status]').forEach(function (el) {
    var status = el.dataset.status || 'ok';
    el.innerHTML = BOX_SVG;
    el.style.background = (STATUS[status] || STATUS.ok).bg;
  });

  /* ── Chip de alerta (DOM-driven) ── */
  function updateAlertChip() {
    var chip = document.getElementById('es-alert-chip');
    if (!chip) return;
    var count = document.querySelectorAll(
      'tr.es-row-esgotado, tr.es-row-abaixo_minimo'
    ).length;
    chip.textContent = count + (count === 1 ? ' abaixo do mínimo' : ' abaixo do mínimo');
    chip.style.display = count > 0 ? '' : 'none';
  }

  /* ── CSRF cookie ── */
  function getCsrf() {
    var c = document.cookie.split(';').find(function (s) {
      return s.trim().startsWith('csrftoken=');
    });
    return c ? c.trim().slice('csrftoken='.length) : '';
  }

  /* ── Atualizar linha da tabela ── */
  function updateRow(itemId, novaQtde, status) {
    var ctrl = document.querySelector('.es-qty-ctrl[data-item-id="' + itemId + '"]');
    if (!ctrl) return;

    var val   = ctrl.querySelector('.es-qty-val');
    var minus = ctrl.querySelector('.es-qty-btn[data-delta="-1"]');
    if (val)   val.textContent = novaQtde;
    if (minus) minus.disabled  = novaQtde === 0;

    var row = ctrl.closest('tr');
    if (row) {
      row.classList.remove('es-row-ok', 'es-row-abaixo_minimo', 'es-row-esgotado');
      row.classList.add('es-row-' + status);

      var badge = row.querySelector('.es-badge');
      if (badge) {
        badge.dataset.status = status;
        badge.textContent    = (STATUS[status] || STATUS.ok).label;
      }

      var avSm = row.querySelector('.es-avatar-sm');
      if (avSm) {
        avSm.dataset.status = status;
        avSm.style.background = (STATUS[status] || STATUS.ok).bg;
      }
    }

    updateAlertChip();
  }

  /* ── Stepper com delegação de evento ── */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.es-qty-btn');
    if (!btn || btn.disabled) return;

    var ctrl   = btn.closest('.es-qty-ctrl');
    if (!ctrl) return;

    var delta  = parseInt(btn.dataset.delta) || 0;
    var itemId = ctrl.dataset.itemId;
    var url    = ctrl.dataset.url;
    if (!delta || !itemId || !url) return;
    e.preventDefault();

    /* Desabilita temporariamente enquanto aguarda resposta */
    btn.disabled = true;

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken':  getCsrf(),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: 'delta=' + delta,
    })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.ok) updateRow(itemId, d.nova_qtde, d.status);
    })
    .catch(function () {})
    .finally(function () {
      /* Re-habilita apenas se não estiver zerado (minus) */
      var val = ctrl.querySelector('.es-qty-val');
      var qtde = val ? parseInt(val.textContent) || 0 : 0;
      if (parseInt(btn.dataset.delta) === -1) {
        btn.disabled = (qtde === 0);
      } else {
        btn.disabled = false;
      }
    });
  });

})();
