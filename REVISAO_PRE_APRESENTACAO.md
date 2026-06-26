# Revisão pré-apresentação — SIGCPC (projeto Django)

Análise feita em 26/06/2026. Itens ordenados por prioridade. Foco no que dá pra resolver hoje e no que **não pode** te pegar de surpresa na banca.

---

## 🔴 Crítico — resolver antes de apresentar

### 1. README não corresponde ao projeto real
O README descreve uma arquitetura que **não existe** no código:
- Estrutura `sigcpc/ → src/ → modules/, hooks/, shared/components/` (estilo Node/React).
- Menciona `package.json` (não existe), `JWT_SECRET`, `DATABASE_URL=postgresql://...sigcpc`.
- O projeto real é **Django**: `apps/core`, `apps/accounts`, templates server-side, `manage.py`.

Se alguém ler o README e tentar rodar/entender, nada bate. As variáveis de ambiente do README (`JWT_SECRET`, `SMTP_PASSWORD`, `DATABASE_URL`) também são diferentes das reais (`SECRET_KEY`, `GROQ_API_KEY`, `DB_NAME`, etc. — ver `.env.example`).

**Ação:** alinhar o README à realidade, ou ao menos a seção de setup e estrutura de pastas. Se não der tempo, evite projetar o README na tela.

### 2. Configuração de banco contraditória
O app **roda em PostgreSQL** (`config/settings/dev.py` e `prod.py` → `base.py`, engine `postgresql`), mas:
- Existe um `db.sqlite3` de 444 KB **com dados, versionado no git**.
- Existe um `config/settings/__init__.py` (185 linhas) inteiro configurado para **SQLite** que **nunca é carregado** (o settings que vale é `config.settings.dev`).

Risco no demo: se a máquina não tiver Postgres com o banco `estagio` no ar, o app não sobe — e o sqlite commitado dá a falsa impressão de "clonou e rodou".

**Ação:** confirme que o Postgres da apresentação está rodando e populado. Decida qual banco é o oficial e remova a configuração do outro. Adicione `db.sqlite3` ao `.gitignore`.

### 3. Reset de senha por e-mail vai falhar com o `.env` atual
No `.env`: `EMAIL_BACKEND=smtp` com `EMAIL_HOST_USER=COLOQUE_SEU_EMAIL_BREVO` (placeholder não preenchido). Se você demonstrar "recuperação de senha", o envio quebra.

**Ação:** ou configure o Brevo de verdade, ou troque para `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` para a demo (o e-mail aparece no terminal).

---

## 🟠 Alto — código morto que pega mal se abrirem o repositório

### 4. Arquivos "fantasma" (sombreados — nunca executam)
- `apps/core/models.py` (219 linhas) — sombreado pela pasta `apps/core/models/`. Contém inclusive o modelo `Projeto` já descontinuado.
- `apps/core/tests.py` (25 linhas) — sombreado pela pasta `apps/core/tests/`.
- `config/settings/__init__.py` (185 linhas) — settings SQLite completo, nunca usado.

**Ação:** apagar os três. Em Python o pacote (pasta) tem precedência sobre o módulo de mesmo nome, então esse código só confunde.

### 5. Templates órfãos (0 referências no código)
- `frontend/templates/chamados/meus.html` (a usada é `meus_chamados.html`)
- `frontend/templates/chamados/novo.html` (a usada é `abrir_tier.html`)
- `frontend/templates/registration/password_reset_code.html`

**Ação:** apagar.

### 6. Imports mortos em `apps/core/views.py`
Importados de `mock_data` e nunca chamados: `proj_kpis`, `proj_por_area`, `proj_por_responsavel`, `proj_por_status_segments`. `MOCK_USUARIOS` é definido em `mock_data.py` e nunca usado. (Só `MOCK_PROJETOS` é usado de fato — para semear o Kanban quando o banco está vazio, o que é legítimo.)

**Ação:** limpar os imports.

---

## 🟡 Médio

### 7. Git com um único commit
Todo o projeto está em um commit "Commit inicial". Sem histórico, e versionando `db.sqlite3`. Se a banca valoriza versionamento, vale mostrar um histórico mínimo. No mínimo, tire o `db.sqlite3` do controle de versão.

### 8. `views.py` monolítico (2.403 linhas)
Um único arquivo mistura CRUD de ativos, estoque, chamados, Kanban e o chat de IA. Não dá pra refatorar hoje, mas tenha a resposta pronta se perguntarem: é um ponto de melhoria conhecido (dividir em módulos por domínio).

### 9. Comentário desatualizado em `ai_context.py`
O topo do arquivo diz "injetado no system_instruction do **Gemini**", mas o provedor primário é o **Groq** (Gemini é fallback, conforme `.env.example` e `views.py`).

---

## 🟢 Polish / cuidado na fala

- **Padronizar nomes de template:** `meus_chamados` vs `meus`, `abrir_tier` vs `novo` — escolher um padrão de nomenclatura.
- **Features no README não implementadas:** o README cita 2FA, WhatsApp, SSO/MFA. Confirme que você não vai prometer na apresentação o que ainda não está pronto — ou apresente claramente como "roadmap".
- `DEBUG=True` no `.env` é esperado em dev; só não esqueça que prod exige `SECRET_KEY` via ambiente.

---

## ✅ O que está bom
- O chat de IA trata ausência/erro de chave de API com mensagens amigáveis (não quebra a tela).
- `.env` **não** está versionado (só `.env.example`) — segredos protegidos.
- Há suíte de testes real em `apps/core/tests/` (authz, chamados, forms, kanban, models).
- `prod.py` tem hardening adequado (SSL redirect, HSTS, cookies secure, X-Frame-Options).
- Sem `print()`, `pdb`, `console.log` ou `TODO/FIXME` espalhados pelo código.

---

### Resumo de 1 minuto para hoje
Antes de apresentar: (1) garanta o Postgres no ar e populado, (2) troque o e-mail para console backend se for demonstrar reset de senha, (3) se sobrar tempo, apague os arquivos fantasma e alinhe o README. O resto é limpeza pós-apresentação.
