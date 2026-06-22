(function () {
  'use strict';

  /* Mapeamento tipo → cores do card header */
  var TIPOS = {
    'site':   { bg: '#2563eb', tagBg: '#eff6ff', tagInk: '#2563eb' },
    'predio': { bg: '#7c3aed', tagBg: '#f5f3ff', tagInk: '#7c3aed' },
    'andar':  { bg: '#ea580c', tagBg: '#fff7ed', tagInk: '#ea580c' },
    'sala':   { bg: '#16a34a', tagBg: '#f0fdf4', tagInk: '#16a34a' },
    'rack':   { bg: '#475569', tagBg: '#f1f5f9', tagInk: '#475569' },
  };

  var avatar  = document.getElementById('lc-avatar');
  var title   = document.getElementById('lc-title');
  var tipoTag = document.getElementById('lc-tipo-tag');
  var nomeInp = document.getElementById('id_nome');
  var tipoSel = document.getElementById('id_tipo');
  var codInp  = document.getElementById('id_codigo');

  /* Normaliza string removendo acentos e colocando em minúsculo */
  function slug(s) {
    return (s || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '');
  }

  /* Atualiza avatar e tag de tipo conforme o select */
  function applyTipo() {
    if (!tipoSel) return;
    var key = slug(tipoSel.value);
    var cfg = TIPOS[key] || { bg: '#94a3b8', tagBg: '#f1f5f9', tagInk: '#64748b' };
    if (avatar)  avatar.style.background = cfg.bg;
    if (tipoTag) {
      tipoTag.textContent      = tipoSel.value || '—';
      tipoTag.style.background = cfg.tagBg;
      tipoTag.style.color      = cfg.tagInk;
    }
  }

  /* Atualiza título do card conforme o nome digitado */
  function applyNome() {
    if (!title || !nomeInp) return;
    title.textContent = nomeInp.value.trim() || 'Novo local';
  }

  if (tipoSel) tipoSel.addEventListener('change', applyTipo);
  if (nomeInp) nomeInp.addEventListener('input', applyNome);

  /* Auto-maiúsculo no campo código */
  if (codInp) {
    codInp.addEventListener('input', function () {
      var pos = this.selectionStart;
      this.value = this.value.toUpperCase();
      this.setSelectionRange(pos, pos);
    });
  }

  /* Estado inicial (importante na página de edição, campos já preenchidos) */
  applyTipo();
  applyNome();

})();
