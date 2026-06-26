from collections import Counter

# ---------------- PROJETOS (MOCK) ----------------
MOCK_PROJETOS = [
    {"id": 1,  "titulo": "Upgrade Wi-Fi",    "responsavel": "Suporte 1", "status": "em_andamento", "coluna_key": "em_andamento", "area": "Infraestrutura de T.I", "percentual": 48.7, "prazo": "2025-10-25", "atrasado": False, "cor": "blue"},
    {"id": 2,  "titulo": "Portal Compras",   "responsavel": "Suporte 2", "status": "em_andamento", "coluna_key": "em_andamento", "area": "Administrativo",       "percentual": 23.0, "prazo": "2025-10-12", "atrasado": True,  "cor": "orange"},
    {"id": 3,  "titulo": "Dash Operacional", "responsavel": "Suporte 3", "status": "em_andamento", "coluna_key": "em_andamento", "area": "Comercial",            "percentual": 22.5, "prazo": "2025-10-30", "atrasado": False, "cor": "purple"},
    {"id": 4,  "titulo": "MES – Produção",   "responsavel": "Suporte 4", "status": "nao_iniciado", "coluna_key": "nao_iniciado", "area": "Controle Industrial",  "percentual": 0.0,  "prazo": "2025-11-30", "atrasado": False, "cor": "gray"},
    {"id": 5,  "titulo": "App Vendas",       "responsavel": "Suporte 5", "status": "nao_iniciado", "coluna_key": "nao_iniciado", "area": "Comercial",            "percentual": 0.0,  "prazo": "2025-11-15", "atrasado": False, "cor": "gray"},
    {"id": 6,  "titulo": "ETL Financeiro",   "responsavel": "Suporte 6", "status": "em_andamento", "coluna_key": "em_andamento", "area": "Administrativo",       "percentual": 4.2,  "prazo": "2025-10-05", "atrasado": True,  "cor": "orange"},
    {"id": 7,  "titulo": "CMMS Manutenção",  "responsavel": "Suporte 7", "status": "concluido",    "coluna_key": "concluido",    "area": "Controle Industrial",  "percentual": 100,  "prazo": "2025-09-20", "atrasado": False, "cor": "green"},
    {"id": 8,  "titulo": "Upgrade ERP",      "responsavel": "Suporte 2", "status": "concluido",    "coluna_key": "concluido",    "area": "Administrativo",       "percentual": 100,  "prazo": "2025-09-05", "atrasado": False, "cor": "green"},
    {"id": 9,  "titulo": "BI de Produção",   "responsavel": "Suporte 1", "status": "em_andamento", "coluna_key": "em_andamento", "area": "Infraestrutura de T.I","percentual": 25.9, "prazo": "2025-10-28", "atrasado": False, "cor": "blue"},
    {"id": 10, "titulo": "Integração WMS",   "responsavel": "Suporte 5", "status": "concluido",    "coluna_key": "concluido",    "area": "Controle Industrial",  "percentual": 100,  "prazo": "2025-08-30", "atrasado": False, "cor": "green"},
]

def proj_kpis(projs):
    t = len(projs)
    concl = sum(1 for p in projs if p["status"] == "concluido")
    anda  = sum(1 for p in projs if p["status"] == "em_andamento")
    nao   = sum(1 for p in projs if p["status"] == "nao_iniciado")
    atras = sum(1 for p in projs if p.get("atrasado"))
    no_prazo = t - atras
    pct_conc = round((concl / t * 100) if t else 0.0, 1)
    return {
        "total": t, "concluidos": concl, "em_andamento": anda, "nao_iniciados": nao,
        "atrasados": atras, "no_prazo": no_prazo, "pct_concluido": pct_conc
    }

def proj_por_status_segments(projs):
    counts = Counter(p["status"] for p in projs)
    total = sum(counts.values()) or 1
    color_map = {
        "em_andamento": "#60a5fa",  # azul
        "concluido":    "#10b981",  # verde
        "nao_iniciado": "#94a3b8",  # cinza
    }
    acc = 0.0
    segs = []
    for label, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        pct = c / total * 100
        segs.append({"label": label, "count": c, "pct": round(pct,1),
                     "start": round(acc,4), "end": round(acc+pct,4),
                     "color": color_map.get(label, "#a78bfa")})
        acc += pct
    return segs, 100.0

def proj_por_responsavel(projs):
    m = {}
    for p in projs:
        r = p["responsavel"]
        mm = m.setdefault(r, {"total":0, "concl":0})
        mm["total"] += 1
        mm["concl"] += 1 if p["status"] == "concluido" else 0
    rows = []
    for r, d in m.items():
        pct = (d["concl"]/d["total"]*100) if d["total"] else 0
        rows.append({"resp": r, "pct": round(pct,1), "concl": d["concl"], "total": d["total"]})
    rows.sort(key=lambda x: (-x["pct"], x["resp"]))
    return rows

def proj_por_area(projs):
    m = {}
    for p in projs:
        a = p["area"]
        d = m.setdefault(a, {"total":0, "anda":0, "concl":0})
        d["total"] += 1
        d["concl"] += 1 if p["status"] == "concluido" else 0
        d["anda"]  += 1 if p["status"] == "em_andamento" else 0
    out = []
    for a, d in m.items():
        pct = (d["concl"]/d["total"]*100) if d["total"] else 0
        out.append({"area": a, "total": d["total"], "anda": d["anda"], "concl": d["concl"], "pct": round(pct,1)})
    out.sort(key=lambda r: (-r["pct"], r["area"]))
    return out
