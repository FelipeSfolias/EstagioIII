<div align="center">

<img src="./public/logo_krindges.png" alt="Krindges" width="140" />

# **SIGCPC**

### _Sistema Integrado de Gestão Patrimonial e Chamados Corporativos_

#### _Um único sistema. Todo o patrimônio. Todas as demandas._

[![Status](https://img.shields.io/badge/Status-Em%20desenvolvimento-F59E0B?style=for-the-badge)](#-roadmap)
[![Versão](https://img.shields.io/badge/Versão-1.4-3B82F6?style=for-the-badge)](#)
[![RBAC](https://img.shields.io/badge/Segurança-RBAC%20%2B%202FA-10B981?style=for-the-badge)](#-segurança-e-conformidade)
[![LGPD](https://img.shields.io/badge/Conformidade-LGPD-7C3AED?style=for-the-badge)](#-segurança-e-conformidade)
[![ISO](https://img.shields.io/badge/Referência-ISO%2FIEC%2027001-06B6D4?style=for-the-badge)](#-segurança-e-conformidade)
[![Licença](https://img.shields.io/badge/Licença-Acadêmica%2FCorporativa-3B82F6?style=for-the-badge)](#-licença)

---

**Trabalho Final de Estágio II — 2025**
Curso de **Ciência da Computação** — Faculdade de Ampére (**FAMPER**)
Empresa concedente: **Krindges Industrial S/A**

</div>

<br>

## ✦ Sumário

- [Sobre o projeto](#-sobre-o-projeto)
- [Contexto acadêmico e empresarial](#-contexto-acadêmico-e-empresarial)
- [O problema](#-o-problema)
- [Módulos do sistema](#-módulos-do-sistema)
- [Atores e papéis (RBAC)](#-atores-e-papéis-rbac)
- [Use Cases](#-use-cases)
- [Arquitetura](#-arquitetura)
- [Stack tecnológica](#-stack-tecnológica)
- [Segurança e conformidade](#-segurança-e-conformidade)
- [Chatbot de IA integrado](#-chatbot-de-ia-integrado)
- [Como executar](#-como-executar)
- [Estrutura de pastas](#-estrutura-de-pastas)
- [Roadmap](#-roadmap)
- [Autores](#-autores)
- [Licença](#-licença)

---

## ✦ Sobre o projeto

O **SIGCPC** — _Sistema Integrado para Controle Patrimonial e Gestão de Chamados e Demandas Corporativas com Chatbot de IA Integrado_ — é uma aplicação web unificada concebida para centralizar a administração patrimonial, o controle de estoque de materiais de expediente e o atendimento de demandas internas (chamados) da **Krindges Industrial S/A**.

A proposta é substituir processos manuais e planilhas descentralizadas por uma plataforma única, auditável e baseada em papéis (RBAC), com painéis gerenciais (Dashboard e Indicadores), fluxo Kanban de projetos e um **chatbot com IA** que orienta o usuário na abertura de chamados e nas consultas de patrimônio.

> Mais do que automatizar rotinas manuais, o sistema busca fornecer maior visibilidade sobre o patrimônio, o estoque e os chamados, apoiando a tomada de decisão e a padronização dos processos.

<br>

## 🎓 Contexto acadêmico e empresarial

| | |
|---|---|
| **Instituição de ensino** | Faculdade de Ampére — **FAMPER** |
| **Curso** | Ciência da Computação |
| **Disciplina** | Estágio Supervisionado II |
| **Empresa concedente** | **Krindges Industrial S/A** (setor têxtil, Ampére/PR) |
| **Ano** | 2025 |
| **Versão do DMS** | 1.4 |

A **Krindges Industrial S/A** foi fundada em **1977** pelos irmãos Renato e Luiz Krindges em **Ampére/PR**. Ao longo das décadas consolidou-se como uma das maiores indústrias têxteis do país, com marcas próprias como **Aicone, Guilherme Ludwig, Docthos e Soul**, atuação no Brasil e Mercosul, e foco em inovação, omnichannel e modernização contínua de seus processos.

O estágio se insere nesse contexto de **transformação digital**, contribuindo diretamente para os fluxos internos de TI e áreas correlatas.

<br>

## ⚠ O problema

Hoje, a Krindges enfrenta dificuldades consideráveis na gestão de bens patrimoniais, materiais de expediente e atendimento de demandas internas:

- **Processos manuais e planilhas descentralizadas** geram inconsistências, extravios e dificultam auditorias.
- **Falta de um sistema unificado de chamados** prejudica o acompanhamento de demandas — de suporte técnico a requisições de compras.
- **Baixa rastreabilidade** das movimentações de ativos e do consumo de estoque.
- **Decisões pouco fundamentadas** por ausência de indicadores consolidados.

O **SIGCPC** responde a esse cenário com um sistema único, auditável e orientado a indicadores.

<br>

## ✦ Módulos do sistema

<table>
<tr>
<td width="33%" valign="top">

### 🏛️ **Patrimônio e Movimentações**
Cadastro completo de dispositivos (modelo, número de série, patrimônio, estado, localidade), comodatos, responsáveis, leitura de **código de barras/QRCode**, anexos (termos, comprovantes) e histórico de movimentações.

</td>
<td width="33%" valign="top">

### 📦 **Materiais e Estoque**
Controle de entradas/saídas, níveis mínimos, **inventário cíclico**, **curva ABC**, consumo por centro de custo, requisições internas e alertas de reposição.

</td>
<td width="33%" valign="top">

### 🎫 **Chamados e Demandas**
Abertura, classificação e roteamento por categoria (Infra, ERP, BI, Compras), **filas por setor**, **SLA configurável** por tipo/prioridade, atribuição manual ou automática e registro de interações no ticket.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 📋 **Kanban de Projetos**
Quadro com colunas _Não iniciado_, _Em andamento_ e _Concluído_. Cartões com título, responsável, área e barra de progresso. Busca por título ou responsável.

</td>
<td width="33%" valign="top">

### 📊 **Indicadores e Dashboard**
KPIs de projetos (totais, % concluído por responsável, área de atuação) e de chamados (por status, prioridade, tipo, conclusão, desempenho por agente, SLA).

</td>
<td width="33%" valign="top">

### 🛒 **Integração com Compras**
Geração de solicitações a partir de chamados de aquisição, validação por orçamento, aprovação por alçada e consolidação de itens para cotação.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🔐 **Autenticação e RBAC**
Login com e-mail/senha, recuperação, sessão via token (`usuarios_tokens_sessao`) e **3 papéis** com permissões distintas. Opção de **2FA**.

</td>
<td width="33%" valign="top">

### 🤖 **Chatbot de IA**
Assistente conversacional para abertura guiada de chamados, consulta a patrimônio e respostas a dúvidas frequentes, integrado ao fluxo principal.

</td>
<td width="33%" valign="top">

### 🔍 **Auditoria**
Logs imutáveis de acesso e alteração, versionamento de registros, segregação de funções e trilhas para conformidade.

</td>
</tr>
</table>

<br>

## 👥 Atores e papéis (RBAC)

O sistema adota **Role-Based Access Control** com três papéis principais (`admin | gestor | usuario`):

| Papel | Responsabilidades |
|:---|:---|
| **Usuário** | Qualquer colaborador autenticado. Abre chamados (UC06) e consulta histórico (UC08). |
| **Suporte / Gestor** | Mantém locais (UC03), ativos (UC04), itens de estoque (UC05), movimenta estoque, trata chamados (UC07) e consulta relatórios. |
| **Administrador** | Todas as permissões do Gestor + administração do sistema, manutenção de usuários (UC02) e ativação/desativação de contas. |

> **Pré-requisito comum:** todos os atores precisam estar autenticados (UC01) antes de executar quaisquer outros casos de uso.

<br>

## ✦ Use Cases

<div align="center">

| ID | Nome | Atores |
|:---:|:---|:---|
| **UC01** | Autenticar Usuário | Todos |
| **UC02** | Manter Usuários | Administrador |
| **UC03** | Manter Locais (hierárquico) | Gestor, Administrador |
| **UC04** | Manter Ativos | Gestor, Administrador |
| **UC05** | Manter Itens de Estoque | Gestor, Administrador |
| **UC06** | Abrir Chamado | Usuário, Gestor, Administrador |
| **UC07** | Tratar Chamado | Gestor, Administrador (Solicitante: apenas comentários) |
| **UC08** | Consultar Histórico e Relatórios | Usuário, Gestor, Administrador |

</div>

<br>

## ✦ Arquitetura

O sistema adota **arquitetura em camadas**, com interface responsiva, serviços de aplicação e persistência relacional única, além de mecanismos nativos de auditoria.

```
┌────────────────────────────────────────────────────────────────┐
│                    Camada de Apresentação                       │
│   ┌──────────┐  ┌────────────────────────────────────────┐    │
│   │ Sidebar  │  │  Header (busca global + logout)         │    │
│   │          │  ├────────────────────────────────────────┤    │
│   │ Menu     │  │   Telas: Login | Dashboard | Usuários   │    │
│   │ Usuário  │  │   Locais | Ativos | Estoque | Kanban    │    │
│   │ Perfil   │  │   Chamados | Indicadores | Relatórios   │    │
│   └──────────┘  └────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │         Camada de Aplicação (Serviços)    │
        │   ┌────────────┐  ┌──────────────────┐   │
        │   │  Auth /    │  │   Patrimônio      │   │
        │   │  RBAC      │  │   Estoque         │   │
        │   │  2FA       │  │   Chamados        │   │
        │   │  Sessão    │  │   Projetos        │   │
        │   └────────────┘  │   Relatórios      │   │
        │                   │   Chatbot IA      │   │
        │                   └──────────────────┘   │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │     Camada de Persistência (Relacional)   │
        │                                           │
        │   usuarios ─── usuarios_tokens_sessao     │
        │   locais (auto-ref pai_id)                │
        │   ativos ─── movimentos_ativos            │
        │   estoque_itens ─── estoque_movimentos    │
        │   chamados (status, prioridade, JSON)     │
        │   projetos (kanban)                       │
        │                                           │
        │   + Logs imutáveis de auditoria           │
        └──────────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────────┐
        │       Integrações Externas                │
        │   • E-mail (notificações de SLA)          │
        │   • WhatsApp (status/prazos/conclusões)   │
        │   • Chatbot IA (LLM)                      │
        └──────────────────────────────────────────┘
```

**Padrões aplicados:** _Arquitetura em camadas_, _RBAC_, _CRUD com auditoria_, _State Machine_ para chamados (`aberto → em_atendimento → resolvido → fechado`), _Auto-referência hierárquica_ para locais, _Soft delete_ via flag `ativo` e _Sessão por token_.

<br>

## ✦ Stack tecnológica

<div align="center">

| Camada | Tecnologia / Padrão | Observação |
|:---|:---|:---|
| **Frontend** | Interface web responsiva | Padronização de fluxos, busca, filtros e ações em massa |
| **Backend** | Serviços de aplicação em camadas | Validação de unicidade, regras de negócio e auditoria |
| **Banco de dados** | Banco relacional | Modelo único compartilhado entre todos os módulos |
| **Autenticação** | Sessão via token + opção de 2FA | Tabela `usuarios_tokens_sessao` com `criado_em`, `expira_em`, `revogado_em` |
| **Controle de acesso** | RBAC (`admin | gestor | usuario`) | Permissões aplicadas por papel |
| **Notificações** | E-mail e WhatsApp | Status, prazos e conclusões de chamados |
| **Identificação** | Código de barras / QRCode | Movimentação rápida de ativos |
| **Modelagem** | UML — Use Cases, Sequência, Classes, DER | Versão 1.4 do DMS |

</div>

<br>

## 🔐 Segurança e conformidade

O SIGCPC foi projetado seguindo boas práticas de segurança da informação e proteção de dados:

- **RBAC** — controle de acesso baseado em papéis com três níveis distintos.
- **2FA opcional** — autenticação multifator com **OTP** disponível para reforço de credenciais sensíveis.
- **Sessões por token** com expiração e revogação registradas (`expira_em`, `revogado_em`).
- **Logs imutáveis** de acesso e alteração para rastreabilidade ponta a ponta.
- **Versionamento de registros** e segregação de funções.
- **Conformidade LGPD** — tratamento de dados pessoais alinhado à legislação brasileira.
- **Trilhas para certificação ISO/IEC 27001** — preparação para auditorias de SGSI.

<br>

## 🤖 Chatbot de IA integrado

O sistema incorpora um **assistente conversacional** alinhado às tendências de transformação digital corporativa. As capacidades previstas incluem:

| Capacidade | O que faz |
|:---|:---|
| **Abertura guiada de chamados** | Conduz o colaborador por perguntas estruturadas, classifica automaticamente categoria/prioridade e gera o ticket. |
| **Consulta de patrimônio** | Responde "onde está o notebook X" ou "quem é o custodiante do ativo Y" em linguagem natural. |
| **Status de chamados** | Informa em tempo real o andamento de tickets do usuário sem precisar navegar pelas telas. |
| **FAQ corporativo** | Responde dúvidas frequentes de TI, RH e Compras com base na documentação interna. |
| **Roteamento inteligente** | Sugere o setor/agente mais adequado para cada demanda com base no histórico. |

> O chatbot é o elemento diferencial de IA do projeto, conectando a interface ao núcleo transacional do sistema sem rupturas no fluxo de trabalho.

<br>

## ✦ Como executar

> ⚠ **Atenção:** este repositório acompanha o **Documento de Modelagem de Sistema (DMS) v1.4**. A configuração de execução depende do stack definitivo escolhido pelos autores. Os passos abaixo são o template recomendado para ambientes web modernos.

### Pré-requisitos

| Ferramenta | Versão mínima | Download |
|:---|:---:|:---|
| **Node.js** | 18.x | https://nodejs.org |
| **npm** ou **yarn** | 9.x / 1.22 | incluso com o Node.js |
| **Banco relacional** | conforme stack | PostgreSQL, MySQL ou equivalente |
| **Git** | qualquer | https://git-scm.com |

### Passos

```bash
# 1. Clonar o repositório
git clone <url-do-repo>
cd sigcpc

# 2. Instalar dependências
npm install

# 3. Configurar variáveis de ambiente
cp .env.example .env.local
# Edite .env.local com as credenciais do banco e serviços externos

# 4. Aplicar migrações do banco
npm run db:migrate

# 5. (Opcional) Popular dados iniciais — usuário admin, locais base
npm run db:seed

# 6. Iniciar o servidor de desenvolvimento
npm run dev
```

### Variáveis de ambiente (referência)

```env
# Banco de dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/sigcpc

# Autenticação
JWT_SECRET=seu-segredo-jwt
SESSION_EXPIRES_IN=8h

# Integrações
SMTP_HOST=smtp.empresa.com
SMTP_USER=notificacoes@krindges.com.br
SMTP_PASSWORD=senha

WHATSAPP_API_TOKEN=token-da-api

# Chatbot
LLM_API_KEY=chave-do-provedor-de-ia
LLM_MODEL=modelo-escolhido
```

<br>

## ✦ Estrutura de pastas (proposta)

```
sigcpc/
├── public/                      # Assets estáticos (logo Krindges, favicon)
├── docs/                        # Documentação acadêmica
│   ├── DMS-v1.4.pdf             # Documento de Modelagem do Sistema
│   ├── diagramas/               # Use cases, sequência, classes, DER
│   └── prototipos/              # Mockups das telas (Figuras 1–13)
├── src/
│   ├── auth/                    # Login, recuperação de senha, 2FA, RBAC
│   ├── modules/
│   │   ├── usuarios/            # UC02 — Manter Usuários
│   │   ├── locais/              # UC03 — hierarquia (pai_id)
│   │   ├── ativos/              # UC04 — patrimônio
│   │   ├── estoque/             # UC05 — itens e movimentações
│   │   ├── chamados/            # UC06 + UC07
│   │   ├── projetos/            # Kanban
│   │   └── relatorios/          # UC08 — histórico e exportações
│   ├── chatbot/                 # Assistente conversacional IA
│   ├── shared/
│   │   ├── components/          # UI compartilhada (cards, tabelas, gráficos)
│   │   ├── hooks/               # Hooks reutilizáveis
│   │   ├── utils/               # Formatters, validators, helpers
│   │   └── notifications/       # E-mail e WhatsApp
│   ├── api/                     # Endpoints HTTP
│   ├── db/
│   │   ├── migrations/          # Versionamento do schema
│   │   ├── seeds/               # Dados iniciais
│   │   └── models/              # Mapeamento das entidades
│   └── audit/                   # Logs imutáveis
├── tests/                       # Testes unitários e de integração
├── .env.example
├── package.json
└── README.md
```

<br>

## ✦ Roadmap

### ✅ Modelado e especificado (DMS v1.4)
- Documento de Modelagem do Sistema completo
- 8 Use Cases descritos com fluxos principais e alternativos
- Diagramas UML (Use Case, Sequência, Classes, DER)
- 13 protótipos de tela (Login, Dashboard, Cadastros, Kanban, Indicadores)
- Regras de negócio identificadas (RN01–RN…)
- Especificação completa dos requisitos funcionais (ERaF), de dados (ERaD) e de interface (ERaI)
- Modelo relacional consolidado

### 🔨 Em desenvolvimento
- Autenticação com RBAC e sessão por token
- Cadastro de usuários, locais (hierárquico) e ativos
- Manutenção de itens de estoque e movimentações
- Abertura e tratamento de chamados
- Kanban de projetos com filtros
- Indicadores de Projetos e de Chamados
- Notificações por e-mail e WhatsApp

### 🔄 Próximos passos (pós-piloto)
- **SSO / MFA** (Single Sign-On e autenticação multifator avançada)
- **Relatórios avançados com drill-down**
- **Automações de reabastecimento** baseadas em níveis mínimos
- **Automações de SLA** com escalonamento por prazo
- **Telemetria** e métricas de uso
- **Testes automatizados** ponta a ponta
- **Refinamento do chatbot** com base no uso real

<br>

## ✦ Autores

<div align="center">

**Felipe Eduardo Sfolias Stachak**
**Luana Eliza Pereira**

_Acadêmicos de Ciência da Computação — FAMPER_

Trabalho Final de **Estágio Supervisionado II — 2025**
Empresa concedente: **Krindges Industrial S/A**

_Ampére, Paraná — 2025_

</div>

<br>

## ✦ Referências da elicitação

Os requisitos do sistema foram obtidos por meio de:
- **Reuniões** com o coordenador de TI da Krindges Industrial S/A
- **Análise** de documentos internos sobre processos patrimoniais e de gestão de demandas
- **Observação direta** das rotinas operacionais
- **Contribuições estruturadas** de usuários-chave das áreas administrativas e técnicas
- **Validação** com o coordenador de estágio acadêmico

<br>

## ✦ Licença

Projeto desenvolvido com finalidade **acadêmica e corporativa**, no contexto do **Estágio Supervisionado II** do curso de Ciência da Computação da FAMPER, em parceria com a **Krindges Industrial S/A**.

O código é disponibilizado para fins de estudo, avaliação acadêmica e uso interno na empresa concedente. Redistribuição, uso comercial externo ou derivação requerem autorização prévia dos autores e da empresa.

<br>

<div align="center">

---

<sub>**SIGCPC** • _Gestão patrimonial, estoque e chamados em uma única fonte de verdade._</sub>
<sub>FAMPER • Krindges Industrial S/A • 2025</sub>

</div>
>>>>>>> f224601415a3b0de9117a6dfdd4eea9dbbc02e00
