(function () {
  'use strict';

  /* ── Cores para avatar (derivadas do nome) ── */
  var COLORS = [
    '#2563eb','#7c3aed','#db2777','#ea580c',
    '#16a34a','#0891b2','#d97706','#9333ea',
  ];

  function initials(name) {
    var parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0][0].toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  function avatarColor(name) {
    var hash = 0;
    for (var i = 0; i < name.length; i++) {
      hash = (hash * 31 + name.charCodeAt(i)) & 0x7fffffff;
    }
    return COLORS[hash % COLORS.length];
  }

  /* ── Avatar grande (header do card de cadastro) ── */
  var bigAvatar    = document.getElementById('fc-avatar');
  var cardTitle    = document.getElementById('fc-title');
  var statusTag    = document.getElementById('fc-status-tag');
  var nomeInput    = document.getElementById('id_nome');
  var loginInput   = document.getElementById('id_username');
  var ativoChk     = document.getElementById('id_ativo');

  function updateAvatar() {
    if (!bigAvatar || !nomeInput) return;
    var name = nomeInput.value.trim();
    bigAvatar.textContent      = name ? initials(name) : '?';
    bigAvatar.style.background = name ? avatarColor(name) : '#94a3b8';
    if (cardTitle) cardTitle.textContent = name || 'Novo funcionário';
  }

  if (nomeInput) {
    nomeInput.addEventListener('input', updateAvatar);
    updateAvatar();
  }

  /* ── Avatares pequenos na tabela ── */
  document.querySelectorAll('.fc-avatar-sm[data-name]').forEach(function (el) {
    var name = el.dataset.name || '';
    el.textContent      = name ? initials(name) : '?';
    el.style.background = name ? avatarColor(name) : '#94a3b8';
  });

  /* ── Tag de status (ativo/inativo) ── */
  function updateStatusTag() {
    if (!statusTag || !ativoChk) return;
    if (ativoChk.checked) {
      statusTag.textContent = 'Ativo';
      statusTag.className   = 'fc-status-tag fc-tag-ativo';
    } else {
      statusTag.textContent = 'Inativo';
      statusTag.className   = 'fc-status-tag fc-tag-inativo';
    }
  }

  if (ativoChk) {
    ativoChk.addEventListener('change', updateStatusTag);
    updateStatusTag();
  }

  /* ── Sugestão de login a partir do nome ── */
  var loginTouched = !!(loginInput && loginInput.value);

  function slugName(name) {
    return name
      .toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z\s]/g, '')
      .trim()
      .split(/\s+/)
      .filter(Boolean);
  }

  if (loginInput) {
    loginInput.addEventListener('input', function () { loginTouched = true; });
  }

  if (nomeInput && loginInput) {
    nomeInput.addEventListener('input', function () {
      if (loginTouched) return;
      var parts = slugName(nomeInput.value);
      if (parts.length === 0) { loginInput.value = ''; return; }
      loginInput.value = parts.length === 1
        ? parts[0]
        : parts[0] + '.' + parts[parts.length - 1];
    });
  }

  /* ── Máscara CPF: 000.000.000-00 ── */
  var cpfInput = document.getElementById('id_cpf');
  if (cpfInput) {
    cpfInput.addEventListener('input', function () {
      var v = this.value.replace(/\D/g, '').slice(0, 11);
      if (v.length > 9)      v = v.replace(/^(\d{3})(\d{3})(\d{3})(\d{0,2})$/, '$1.$2.$3-$4');
      else if (v.length > 6) v = v.replace(/^(\d{3})(\d{3})(\d{0,3})$/, '$1.$2.$3');
      else if (v.length > 3) v = v.replace(/^(\d{3})(\d{0,3})$/, '$1.$2');
      this.value = v;
    });
  }

  /* ── Máscara Telefone: (00) 90000-0000 ── */
  var telInput = document.getElementById('id_contato');
  if (telInput) {
    telInput.addEventListener('input', function () {
      var v = this.value.replace(/\D/g, '').slice(0, 11);
      if (v.length > 10)     v = v.replace(/^(\d{2})(\d{5})(\d{0,4})$/, '($1) $2-$3');
      else if (v.length > 6) v = v.replace(/^(\d{2})(\d{4})(\d{0,5})$/, '($1) $2-$3');
      else if (v.length > 2) v = v.replace(/^(\d{2})(\d{0,5})$/, '($1) $2');
      else                   v = v.replace(/^(\d*)$/, '($1');
      this.value = v;
    });
  }

  /* ── Mostrar / ocultar senha ── */
  document.querySelectorAll('.fc-eye-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var inp = document.getElementById(this.dataset.target);
      if (!inp) return;
      var show = inp.type === 'password';
      inp.type = show ? 'text' : 'password';
      this.setAttribute('aria-label', show ? 'Ocultar senha' : 'Mostrar senha');
      var icon = this.querySelector('.fc-eye-icon');
      if (icon) icon.style.opacity = show ? '.4' : '1';
    });
  });

  /* ── Conferência de senha em tempo real ── */
  var senhaInp    = document.getElementById('id_nova_senha');
  var confirmaInp = document.getElementById('id_confirmar_senha');

  function syncPassCheck() {
    if (!senhaInp || !confirmaInp) return;
    var fg = confirmaInp.closest('.fg');
    if (!fg) return;
    var msg = fg.querySelector('.fc-pass-match');
    if (!msg) {
      msg = document.createElement('span');
      msg.className = 'fc-error fc-pass-match';
      fg.appendChild(msg);
    }
    if (!confirmaInp.value) {
      msg.textContent = '';
      fg.classList.remove('has-error');
      return;
    }
    if (senhaInp.value !== confirmaInp.value) {
      msg.textContent = 'As senhas não conferem.';
      fg.classList.add('has-error');
    } else {
      msg.textContent = '';
      fg.classList.remove('has-error');
    }
  }

  if (senhaInp)    senhaInp.addEventListener('input', syncPassCheck);
  if (confirmaInp) confirmaInp.addEventListener('input', syncPassCheck);

})();
