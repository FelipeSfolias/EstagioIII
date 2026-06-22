import json
import logging
import re
import time

from datetime import timedelta, date as date_type

logger = logging.getLogger(__name__)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models as db_models
from django.http import Http404, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .authz import tier_required
from .ai_context import montar_system_prompt
from django.db.models.deletion import ProtectedError
from .models import (
    Quadro, Lista, Etiqueta, Cartao, ChecklistKanban, ItemChecklistKanban, AtividadeCartao,
    KanbanColuna, KanbanCard, KanbanAuditLog,
    Funcionario, Ativo, Local, ItemEstoque, Chamado, HistoricoChamado, AnexoChamado,
    Departamento, Topico,
)
from .forms import (
    AbrirChamadoForm,
    AtivoForm,
    FuncionarioForm,
    ItemEstoqueForm,
    LocalForm,
    ResponderChamadoForm,
)
from .mock_data import (
    MOCK_PROJETOS,
    proj_kpis,
    proj_por_area,
    proj_por_responsavel,
    proj_por_status_segments,
)

# ============================================================
# CONSTANTES / HELPERS
# ============================================================

SETOR_OPCOES = ["Produção", "PPCP", "Demanda", "Compras", "TI", "Estoque", "Engenharia", "Modelagem", "Corte"]



def _chat_reply_and_state(msg, state):
    m = (msg or "").strip()
    ml = m.lower()

    if any(w in ml for w in ["ajuda", "opções", "opcoes", "menu"]):
        return (
            "Posso ajudar com:\n"
            "• diagnosticar problemas (ex.: \"wifi caiu\", \"sem acesso ao ERP\")\n"
            "• abrir um chamado (diga \"abrir chamado\")\n"
            "• acompanhar chamados (acesse: Meus Chamados)"
        ), state

    if "wifi" in ml or "wi-fi" in ml:
        return (
            "Entendi: problema de Wi-Fi. Tente:\n"
            "1) Reiniciar o adaptador de rede\n"
            "2) Esquecer e reconectar à rede\n"
            "3) Se persistir, digite **abrir chamado**"
        ), state

    if "erp" in ml:
        return (
            "Sem acesso ao ERP? Verifique VPN/AD. Se continuar, digite **abrir chamado** "
            "para eu registrar pro time de TI."
        ), state

    if "notebook" in ml or "lento" in ml or "travando" in ml:
        return (
            "Notebook lento: feche apps pesados, limpe arquivos temporários. "
            "Se não resolver, digite **abrir chamado**."
        ), state

    if "abrir chamado" in ml or "criar chamado" in ml:
        state = {"step": "assunto"}
        return "Perfeito, vamos abrir um chamado! Qual é o **assunto**?", state

    if state and state.get("step") == "assunto":
        state["assunto"] = m
        state["step"] = "origem"
        return "Certo. Qual é a **origem**? (Infra | Suporte | ERP | Manutenção | Outros)", state

    if state and state.get("step") == "origem":
        mapa = {
            "infra": "Infra", "suporte": "Suporte", "erp": "ERP",
            "manutencao": "Manutenção", "manutenção": "Manutenção", "outros": "Outros",
        }
        state["origem"] = mapa.get(m.lower(), m.capitalize() or "Outros")
        state["step"] = "descricao"
        return "Anotei. Agora descreva o problema com **detalhes**:", state

    if state and state.get("step") == "descricao":
        state["descricao"] = m
        from django.contrib.auth.models import User as _User
        user_obj = None
        username = state.get("username", "")
        if username:
            user_obj = _User.objects.filter(username=username).first()
        chamado_obj = Chamado.objects.create(
            assunto=state["assunto"],
            descricao=state["descricao"],
            origem=state["origem"],
            prioridade="baixa",
            aberto_por=user_obj,
            agente=None,
        )
        state = {}
        return (
            f"Chamado **#{chamado_obj.pk}** aberto!\n"
            f"Assunto: {chamado_obj.assunto}\n"
            f"Origem: {chamado_obj.origem}\n"
            "Você pode acompanhar em **Meus Chamados**."
        ), state

    return (
        "Não tenho certeza se entendi. Você pode tentar: **abrir chamado**, "
        "**ajuda** ou descrever o problema (ex.: \"wifi caiu\")."
    ), state


# ============================================================
# ADMIN ONLY
# ============================================================

@login_required
@tier_required("admin")
def dashboard(request):
    hoje = timezone.now()
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    MESES = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
    ]
    periodo = f"{MESES[hoje.month - 1]} / {hoje.year}"

    qs = Chamado.objects.filter(aberto_em__gte=inicio_mes)
    total     = qs.count()
    aberto    = qs.filter(status="aberto").count()
    em_atend  = qs.filter(status="em_atendimento").count()
    resolvido = qs.filter(status="resolvido").count()
    pendentes = aberto + em_atend

    prioridade_alta  = qs.filter(prioridade="alta").count()
    prioridade_media = qs.filter(prioridade="media").count()
    prioridade_baixa = qs.filter(prioridade="baixa").count()

    dentro_sla = fora_sla = 0
    for c in qs.filter(status__in=["resolvido", "fechado"], fechado_em__isnull=False):
        elapsed_h = (c.fechado_em - c.aberto_em).total_seconds() / 3600
        if elapsed_h <= c.sla_horas:
            dentro_sla += 1
        else:
            fora_sla += 1

    kpi = {
        "total": total, "aberto": aberto, "em_atendimento": em_atend,
        "resolvido": resolvido, "pendentes": pendentes,
        "prioridade_alta": prioridade_alta, "prioridade_media": prioridade_media,
        "prioridade_baixa": prioridade_baixa,
        "dentro_sla": dentro_sla, "fora_sla": fora_sla,
    }

    def _seg(label, count, total_n, cor, acc):
        pct = round(count / (total_n or 1) * 100, 1)
        return {
            "label": label, "count": count, "cor": cor,
            "pct_fmt": f"{pct:.1f}".replace(".", ","),
            "dasharray": f"{pct} {round(100 - pct, 1)}",
            "dashoffset": "0" if acc < 0.001 else f"{-acc:.1f}",
        }, pct

    concluidos_n     = qs.filter(status__in=["resolvido", "fechado"]).count()
    nao_concluidos_n = total - concluidos_n
    conclusao_segments, acc = [], 0.0
    for lbl, cnt, cor in [
        ("Concluídos", concluidos_n, "#16a34a"),
        ("Não concluídos", nao_concluidos_n, "#dc2626"),
    ]:
        seg, pct = _seg(lbl, cnt, total, cor, acc)
        conclusao_segments.append(seg)
        acc += pct

    cartoes        = Cartao.objects.all()
    total_proj     = cartoes.count()
    proj_concluido = cartoes.filter(concluido=True).count()
    proj_atrasado  = cartoes.filter(
        concluido=False, data_entrega__isnull=False, data_entrega__lt=hoje
    ).count()
    proj_em_andamento = cartoes.filter(concluido=False, progresso__gt=0).exclude(
        data_entrega__isnull=False, data_entrega__lt=hoje
    ).count()
    proj_nao_iniciado = cartoes.filter(concluido=False, progresso=0).exclude(
        data_entrega__isnull=False, data_entrega__lt=hoje
    ).count()

    proj_segments, acc2 = [], 0.0
    for lbl, cnt, cor in [
        ("Não iniciado", proj_nao_iniciado, "#475569"),
        ("Em andamento", proj_em_andamento, "#2563eb"),
        ("Concluído",    proj_concluido,    "#16a34a"),
        ("Atrasado",     proj_atrasado,     "#dc2626"),
    ]:
        seg, pct = _seg(lbl, cnt, total_proj, cor, acc2)
        proj_segments.append(seg)
        acc2 += pct

    def _quando(dt):
        delta = hoje - dt
        s = int(delta.total_seconds())
        if s < 3600:
            return f"há {max(1, s // 60)}min"
        if s < 86400:
            return f"há {s // 3600}h"
        return f"há {delta.days}d"

    recentes = []
    for c in Chamado.objects.select_related("agente", "agente__funcionario").order_by("-aberto_em")[:6]:
        if c.agente:
            try:
                nome_agente = c.agente.funcionario.nome
            except Exception:
                nome_agente = c.agente.get_full_name() or c.agente.username
        else:
            nome_agente = None
        recentes.append({
            "pk": c.pk, "assunto": c.assunto,
            "prioridade": c.prioridade, "prioridade_label": c.get_prioridade_display(),
            "status": c.status, "status_label": c.get_status_display(),
            "agente": nome_agente, "quando": _quando(c.aberto_em),
        })

    return render(request, "dashboard.html", {
        "kpi": kpi,
        "conclusao_segments": conclusao_segments,
        "total_chamados": total,
        "proj_segments": proj_segments,
        "total_proj": total_proj,
        "recentes": recentes,
        "periodo": periodo,
    })


@login_required
@tier_required("admin")
def cad_usuarios(request):
    if request.method == "POST":
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            func = form.save()
            messages.success(request, f"Funcionário '{func.nome}' cadastrado.")
            return redirect("core:cad_usuarios")
    else:
        form = FuncionarioForm()

    qs = Funcionario.objects.select_related("ativo_atribuido", "usuario").all()

    q = (request.GET.get("q") or "").strip()
    f_setor = (request.GET.get("setor") or "").strip()
    f_ativo = (request.GET.get("ativo") or "").strip()

    if q:
        qs = qs.filter(
            db_models.Q(nome__icontains=q)
            | db_models.Q(email__icontains=q)
            | db_models.Q(cpf__icontains=q)
            | db_models.Q(funcao__icontains=q)
        )
    if f_setor:
        qs = qs.filter(setor__iexact=f_setor)
    if f_ativo in ("sim", "nao"):
        qs = qs.filter(ativo=(f_ativo == "sim"))

    setores = Funcionario.objects.values_list("setor", flat=True).distinct().order_by("setor")

    return render(request, "cadastros/usuarios.html", {
        "form": form,
        "usuarios": qs,
        "setores": setores,
        "sel_setor": f_setor,
        "sel_ativo": f_ativo,
    })


@login_required
@tier_required("admin")
def usuario_editar(request, uid: int):
    func = get_object_or_404(Funcionario, pk=uid)
    if request.method == "POST":
        form = FuncionarioForm(request.POST, instance=func)
        if form.is_valid():
            form.save()
            messages.success(request, f"Funcionário '{func.nome}' atualizado.")
            return redirect("core:cad_usuarios")
    else:
        form = FuncionarioForm(instance=func)
    return render(request, "cadastros/usuario_editar.html", {"form": form, "func": func})


@login_required
@tier_required("admin")
def usuario_excluir(request, uid: int):
    func = get_object_or_404(Funcionario, pk=uid)
    if request.method == "POST":
        nome = func.nome
        func.delete()
        messages.success(request, f"Funcionário '{nome}' excluído.")
    return redirect("core:cad_usuarios")


@login_required
@tier_required("admin")
def cad_locais(request):
    if request.method == "POST":
        form = LocalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Local '{form.cleaned_data['nome']}' salvo.")
            return redirect("core:cad_locais")
    else:
        form = LocalForm()

    q = (request.GET.get("q") or "").strip()
    f_tipo = (request.GET.get("tipo") or "").strip()
    f_pai = (request.GET.get("pai") or "").strip()
    f_id = (request.GET.get("id") or "").strip()

    qs = Local.objects.select_related("pai__pai__pai__pai")
    if q:
        qs = qs.filter(
            db_models.Q(codigo__icontains=q)
            | db_models.Q(nome__icontains=q)
            | db_models.Q(tipo__icontains=q)
        )
    if f_tipo:
        qs = qs.filter(tipo__iexact=f_tipo)
    if f_pai == "raiz":
        qs = qs.filter(pai__isnull=True)
    elif f_pai == "compai":
        qs = qs.filter(pai__isnull=False)
    if f_id:
        try:
            qs = qs.filter(pk=int(f_id))
        except ValueError:
            qs = qs.none()

    tipos = Local.objects.values_list("tipo", flat=True).distinct().order_by("tipo")
    return render(request, "cadastros/locais.html", {
        "form": form, "locais": qs, "tipos": tipos,
        "sel_tipo": f_tipo, "sel_pai": f_pai, "sel_id": f_id,
    })


@login_required
@tier_required("admin")
def local_editar(request, lid: int):
    local = get_object_or_404(Local, pk=lid)
    if request.method == "POST":
        form = LocalForm(request.POST, instance=local)
        if form.is_valid():
            form.save()
            messages.success(request, f"Local '{local.nome}' atualizado.")
            return redirect("core:cad_locais")
    else:
        form = LocalForm(instance=local)
    return render(request, "cadastros/local_editar.html", {"form": form, "local": local})


@login_required
@tier_required("admin")
@require_POST
def local_excluir(request, lid: int):
    local = get_object_or_404(Local, pk=lid)
    nome = local.nome
    try:
        local.delete()
        messages.success(request, f"Local '{nome}' excluído.")
    except ProtectedError:
        messages.error(request, f"Não é possível excluir '{nome}': há ativos vinculados.")
    return redirect("core:cad_locais")


@login_required
@tier_required("admin")
def cad_ativos(request):
    if request.method == "POST":
        form = AtivoForm(request.POST)
        custodiante_id = (request.POST.get("custodiante_id") or "").strip()
        if form.is_valid():
            ativo = form.save()
            _ativo_assign_custodiante(ativo, custodiante_id)
            messages.success(request, f"Ativo '{ativo.patrimonio}' salvo.")
            return redirect("core:cad_ativos")
    else:
        form = AtivoForm()

    q = (request.GET.get("q") or "").strip()
    f_tipo = (request.GET.get("tipo") or "").strip()
    f_estado = (request.GET.get("estado") or "").strip()

    qs = Ativo.objects.select_related("local").prefetch_related("custodiantes").all()
    if q:
        qs = qs.filter(
            db_models.Q(patrimonio__icontains=q)
            | db_models.Q(modelo__icontains=q)
            | db_models.Q(numero_serie__icontains=q)
            | db_models.Q(custodiantes__nome__icontains=q)
        ).distinct()
    if f_tipo:
        qs = qs.filter(categoria=f_tipo)
    if f_estado:
        qs = qs.filter(estado=f_estado)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "cadastros/ativos.html", {
        "form": form,
        "ativos": page_obj,
        "total_ativos": paginator.count,
        "page_obj": page_obj,
        "categorias": Ativo.CATEGORIAS,
        "estados": Ativo.ESTADOS,
        "sel_tipo": f_tipo,
        "sel_estado": f_estado,
    })


@login_required
@tier_required("admin")
def ativo_editar(request, aid: int):
    ativo = get_object_or_404(Ativo, pk=aid)
    if request.method == "POST":
        form = AtivoForm(request.POST, instance=ativo)
        custodiante_id = (request.POST.get("custodiante_id") or "").strip()
        if form.is_valid():
            form.save()
            _ativo_assign_custodiante(ativo, custodiante_id)
            messages.success(request, f"Ativo '{ativo.patrimonio}' atualizado.")
            return redirect("core:cad_ativos")
    else:
        form = AtivoForm(instance=ativo)
    custodiante_atual = ativo.custodiantes.first()
    return render(request, "cadastros/ativo_editar.html", {
        "form": form,
        "ativo": ativo,
        "custodiante_atual": custodiante_atual,
    })


@login_required
@tier_required("admin")
@require_POST
def ativo_excluir(request, aid: int):
    ativo = get_object_or_404(Ativo, pk=aid)
    pat = ativo.patrimonio
    ativo.delete()
    messages.success(request, f"Ativo '{pat}' excluído.")
    return redirect("core:cad_ativos")


@login_required
@tier_required("admin")
def cad_itens_estoque(request):
    if request.method == "POST":
        form = ItemEstoqueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item '{form.cleaned_data['nome']}' salvo.")
            return redirect("core:cad_itens_estoque")
    else:
        form = ItemEstoqueForm()

    q = (request.GET.get("q") or "").strip()
    f_uni = (request.GET.get("unidade") or "").strip()
    f_status = (request.GET.get("status") or "").strip()

    qs = ItemEstoque.objects.all()
    if q:
        qs = qs.filter(
            db_models.Q(sku__icontains=q) | db_models.Q(nome__icontains=q)
        )
    if f_uni:
        qs = qs.filter(unidade__iexact=f_uni)
    if f_status == "esgotado":
        qs = qs.filter(qtde=0)
    elif f_status == "abaixo_minimo":
        qs = qs.filter(qtde__gt=0, qtde__lt=db_models.F("nivel_minimo"))
    elif f_status == "ok":
        qs = qs.filter(qtde__gte=db_models.F("nivel_minimo"))

    alerta_count = ItemEstoque.objects.filter(qtde__lt=db_models.F("nivel_minimo")).count()
    unidades = ItemEstoque.objects.values_list("unidade", flat=True).distinct().order_by("unidade")

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "cadastros/itens_estoque.html", {
        "form": form,
        "itens": page_obj,
        "total_itens": paginator.count,
        "page_obj": page_obj,
        "alerta_count": alerta_count,
        "unidades": unidades,
        "sel_unidade": f_uni,
        "sel_status": f_status,
    })


@login_required
@tier_required("admin")
def item_editar(request, iid: int):
    item = get_object_or_404(ItemEstoque, pk=iid)
    if request.method == "POST":
        form = ItemEstoqueForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item '{item.nome}' atualizado.")
            return redirect("core:cad_itens_estoque")
    else:
        form = ItemEstoqueForm(instance=item)
    return render(request, "cadastros/item_estoque_editar.html", {
        "form": form,
        "item": item,
    })


@login_required
@tier_required("admin")
@require_POST
def item_excluir(request, iid: int):
    item = get_object_or_404(ItemEstoque, pk=iid)
    nome = item.nome
    item.delete()
    messages.success(request, f"Item '{nome}' excluído.")
    return redirect("core:cad_itens_estoque")


@login_required
@tier_required("admin")
@require_POST
def item_ajustar_qtde(request, iid: int):
    from django.db import transaction as db_transaction
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    try:
        delta = int(request.POST.get("delta", 0))
    except (ValueError, TypeError):
        delta = 0
    if delta not in (1, -1):
        if is_ajax:
            return JsonResponse({"ok": False}, status=400)
        return redirect("core:cad_itens_estoque")
    with db_transaction.atomic():
        item = get_object_or_404(ItemEstoque.objects.select_for_update(), pk=iid)
        item.qtde = max(0, item.qtde + delta)
        item.save(update_fields=["qtde"])
    if is_ajax:
        return JsonResponse({"ok": True, "nova_qtde": item.qtde, "status": item.status_estoque})
    return redirect("core:cad_itens_estoque")


@login_required
def ativo_buscar(request):
    q = (request.GET.get("q") or "").strip()
    qs = Ativo.objects.all()
    if q:
        qs = qs.filter(
            db_models.Q(patrimonio__icontains=q) | db_models.Q(modelo__icontains=q)
        )
    qs = qs.order_by("patrimonio")[:20]
    data = [
        {"id": a.id, "patrimonio": a.patrimonio, "modelo": a.modelo, "categoria": a.categoria}
        for a in qs
    ]
    return JsonResponse({"results": data})


@login_required
@tier_required("admin")
def funcionario_buscar(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"results": []})
    qs = (
        Funcionario.objects
        .filter(ativo=True)
        .filter(
            db_models.Q(nome__icontains=q)
            | db_models.Q(setor__icontains=q)
            | db_models.Q(email__icontains=q)
        )
        .order_by("nome")[:8]
    )
    results = [
        {"id": f.pk, "nome": f.nome, "setor": f.setor, "email": f.email}
        for f in qs
    ]
    return JsonResponse({"results": results})


def _ativo_assign_custodiante(ativo, custodiante_id):
    Funcionario.objects.filter(ativo_atribuido=ativo).update(ativo_atribuido=None)
    if custodiante_id:
        try:
            func = Funcionario.objects.get(pk=int(custodiante_id), ativo=True)
            func.ativo_atribuido = ativo
            func.save(update_fields=["ativo_atribuido"])
        except (Funcionario.DoesNotExist, ValueError):
            pass


@login_required
@tier_required("admin")
def ativo_proximo_patrimonio(request):
    categoria = request.GET.get("categoria", "").strip()
    sugestao = Ativo.proximo_patrimonio(categoria) if categoria else ""
    return JsonResponse({"patrimonio": sugestao})


def _pat_page_range(current, total):
    if total <= 7:
        return list(range(1, total + 1))
    core = {max(1, current - 1), current, min(total, current + 1)}
    pages = sorted({1, total} | core)
    result, prev = [], 0
    for p in pages:
        if p - prev > 1:
            result.append(-1)   # sentinel → ellipsis
        result.append(p)
        prev = p
    return result


@login_required
@tier_required("admin")
def patrimonios_lista(request):
    q           = (request.GET.get("q")         or "").strip()
    f_categoria = (request.GET.get("categoria")  or "").strip()
    f_estado    = (request.GET.get("estado")     or "").strip()
    f_local     = (request.GET.get("local")      or "").strip()
    try:
        per_page = min(max(int(request.GET.get("per_page") or 12), 1), 100)
    except (ValueError, TypeError):
        per_page = 12
    try:
        page_num = max(int(request.GET.get("page") or 1), 1)
    except (ValueError, TypeError):
        page_num = 1

    qs = Ativo.objects.select_related("local").prefetch_related("custodiantes").all()

    if q:
        qs = qs.filter(
            db_models.Q(patrimonio__icontains=q)
            | db_models.Q(modelo__icontains=q)
            | db_models.Q(numero_serie__icontains=q)
            | db_models.Q(custodiantes__nome__icontains=q)
        ).distinct()
    if f_categoria:
        qs = qs.filter(categoria=f_categoria)
    if f_estado:
        qs = qs.filter(estado=f_estado)
    if f_local:
        try:
            qs = qs.filter(local_id=int(f_local))
        except ValueError:
            pass

    base = Ativo.objects
    kpi = {
        "total":      base.count(),
        "em_uso":     base.filter(estado="em_uso").count(),
        "disponivel": base.filter(estado="estoque").count(),
        "manutencao": base.filter(estado="manutencao").count(),
        "baixado":    base.filter(estado="descartado").count(),
    }

    paginator  = Paginator(qs, per_page)
    page_obj   = paginator.get_page(page_num)
    page_range = _pat_page_range(page_obj.number, paginator.num_pages)

    return render(request, "patrimonios/lista.html", {
        "page_obj":       page_obj,
        "ativos":         page_obj.object_list,
        "total_filtered": paginator.count,
        "busca":          q,
        "categorias":     Ativo.CATEGORIAS,
        "estados":        Ativo.ESTADOS,
        "locais":         Local.objects.order_by("nome"),
        "sel_categoria":  f_categoria,
        "sel_estado":     f_estado,
        "sel_local":      f_local,
        "per_page":       per_page,
        "kpi":            kpi,
        "page_range":     page_range,
    })


# ============================================================
# SUPORTE + ADMIN
# ============================================================

@login_required
@tier_required("suporte", "admin")
def chamados_indicadores(request):
    hoje = timezone.localdate()

    # ── Período com persistência em sessão ───────────────────────
    if request.GET.get("limpar"):
        request.session.pop("ind_inicio", None)
        request.session.pop("ind_fim", None)
        return redirect("core:chamados_indicadores")

    def _parse_date(s):
        try:
            return date_type.fromisoformat(s) if s else None
        except ValueError:
            return None

    inicio_param = _parse_date(request.GET.get("inicio", ""))
    fim_param    = _parse_date(request.GET.get("fim", ""))

    if inicio_param or fim_param:
        inicio = inicio_param or hoje.replace(day=1)
        fim    = fim_param    or hoje
        if inicio > fim:
            inicio, fim = fim, inicio
        request.session["ind_inicio"] = inicio.isoformat()
        request.session["ind_fim"]    = fim.isoformat()
    else:
        inicio = _parse_date(request.session.get("ind_inicio")) or hoje.replace(day=1)
        fim    = _parse_date(request.session.get("ind_fim"))    or hoje

    if fim > hoje:
        fim = hoje

    qs = Chamado.objects.filter(aberto_em__date__gte=inicio, aberto_em__date__lte=fim)
    total = qs.count()

    aberto   = qs.filter(status="aberto").count()
    em_atend = qs.filter(status="em_atendimento").count()
    resolvido = qs.filter(status__in=["resolvido", "fechado"]).count()

    res_list = list(qs.filter(
        status__in=["resolvido", "fechado"], fechado_em__isnull=False
    ).values("aberto_em", "fechado_em", "sla_horas"))
    dentro_sla = sum(
        1 for c in res_list
        if (c["fechado_em"] - c["aberto_em"]).total_seconds() / 3600 <= (c["sla_horas"] or 8)
    )

    kpi = {
        "total":           total,
        "aberto":          aberto,
        "em_atendimento":  em_atend,
        "resolvido":       resolvido,
        "pendentes":       aberto + em_atend,
        "prioridade_alta":  qs.filter(prioridade="alta").count(),
        "prioridade_media": qs.filter(prioridade="media").count(),
        "prioridade_baixa": qs.filter(prioridade="baixa").count(),
        "dentro_sla": dentro_sla,
        "fora_sla":   len(res_list) - dentro_sla,
    }

    CORES_TIPO = ["#2563eb", "#16a34a", "#7c3aed", "#ea580c", "#0d9488", "#ca8a04", "#dc2626"]
    por_tipo_raw = list(qs.values("origem").annotate(total=db_models.Count("id")).order_by("-total"))
    total_tipo = sum(t["total"] for t in por_tipo_raw) or 1
    por_tipo = [
        {
            "nome": t["origem"],
            "total": t["total"],
            "percentual": round(t["total"] / total_tipo * 100, 1),
            "cor": CORES_TIPO[i % len(CORES_TIPO)],
        }
        for i, t in enumerate(por_tipo_raw)
    ]

    total_c = total or 1
    conclusao = {
        "concluidos":        resolvido,
        "nao_concluidos":    total - resolvido,
        "pct_concluidos":    round(resolvido / total_c * 100, 1),
        "pct_nao_concluidos": round((total - resolvido) / total_c * 100, 1),
    }

    delta_dias = (fim - inicio).days
    dias_range = [inicio + timedelta(days=i) for i in range(delta_dias + 1)]
    # Labels: dia/mês quando período cruza meses, só dia quando é tudo no mesmo mês
    mesmo_mes = inicio.month == fim.month and inicio.year == fim.year
    labels_linha = [str(d.day) if mesmo_mes else d.strftime("%d/%m") for d in dias_range]
    criados_map = {
        c["aberto_em__date"]: c["total"]
        for c in Chamado.objects.filter(aberto_em__date__gte=inicio, aberto_em__date__lte=fim)
            .values("aberto_em__date").annotate(total=db_models.Count("id"))
    }
    fechados_map = {
        c["fechado_em__date"]: c["total"]
        for c in Chamado.objects.filter(
            fechado_em__date__gte=inicio, fechado_em__date__lte=fim,
            status__in=["resolvido", "fechado"]
        ).values("fechado_em__date").annotate(total=db_models.Count("id"))
    }
    grafico_linha = {
        "dias":       json.dumps(labels_linha),
        "criados":    json.dumps([criados_map.get(d, 0) for d in dias_range]),
        "resolvidos": json.dumps([fechados_map.get(d, 0) for d in dias_range]),
    }

    por_equipe = []
    for row in qs.values("origem").annotate(
        pendentes=db_models.Count("id", filter=db_models.Q(status__in=["aberto", "em_atendimento"])),
        resolvidos=db_models.Count("id", filter=db_models.Q(status__in=["resolvido", "fechado"])),
    ).order_by("origem"):
        tot = row["pendentes"] + row["resolvidos"]
        pct = round(row["resolvidos"] / tot * 100, 1) if tot else 0.0
        por_equipe.append({
            "nome": row["origem"], "pend_ret": 0,
            "pendentes": row["pendentes"], "resolvidos": row["resolvidos"],
            "percentual": pct, "subtipos": [],
        })

    totais_equipe = {
        "pend_ret":   0,
        "pendentes":  sum(e["pendentes"]  for e in por_equipe),
        "resolvidos": sum(e["resolvidos"] for e in por_equipe),
        "percentual": round(resolvido / total_c * 100, 1),
    }

    agente_data = {}
    for c in qs.filter(agente__isnull=False).values(
        "agente_id", "agente__first_name", "agente__last_name", "agente__username",
        "status", "aberto_em", "fechado_em", "sla_horas",
    ):
        aid = c["agente_id"]
        if aid not in agente_data:
            nome = f"{c['agente__first_name']} {c['agente__last_name']}".strip() or c["agente__username"]
            agente_data[aid] = {"nome": nome, "pendentes": 0, "resolvidos": 0, "sla_ok": 0, "sla_total": 0}
        d = agente_data[aid]
        if c["status"] in ("aberto", "em_atendimento"):
            d["pendentes"] += 1
        elif c["status"] in ("resolvido", "fechado"):
            d["resolvidos"] += 1
            if c["fechado_em"]:
                horas = (c["fechado_em"] - c["aberto_em"]).total_seconds() / 3600
                d["sla_total"] += 1
                if horas <= (c["sla_horas"] or 8):
                    d["sla_ok"] += 1

    por_colaborador = sorted([
        {
            "nome": d["nome"], "pend_ret": 0,
            "pendentes":    d["pendentes"],
            "resolvidos":   d["resolvidos"],
            "pct_conclusao": round(d["resolvidos"] / max(d["pendentes"] + d["resolvidos"], 1) * 100, 1),
            "pct_sla":       round(d["sla_ok"] / d["sla_total"] * 100, 1) if d["sla_total"] else 0.0,
        }
        for d in agente_data.values()
    ], key=lambda x: x["resolvidos"], reverse=True)

    n = len(por_colaborador) or 1
    totais_colab = {
        "pend_ret":     0,
        "pendentes":    sum(c["pendentes"]  for c in por_colaborador),
        "resolvidos":   sum(c["resolvidos"] for c in por_colaborador),
        "pct_conclusao": round(sum(c["pct_conclusao"] for c in por_colaborador) / n, 1),
        "pct_sla":       round(sum(c["pct_sla"]       for c in por_colaborador) / n, 1),
    }

    return render(request, "chamados/indicadores.html", {
        "kpi":             kpi,
        "por_tipo":        por_tipo,
        "conclusao":       conclusao,
        "grafico_linha":   grafico_linha,
        "por_equipe":      por_equipe,
        "totais_equipe":   totais_equipe,
        "por_colaborador": por_colaborador,
        "totais_colab":    totais_colab,
        "inicio":          inicio.isoformat(),
        "fim":             fim.isoformat(),
        "periodo_label":   f"{inicio.strftime('%d/%m/%Y')} – {fim.strftime('%d/%m/%Y')}",
    })


def _seed_kanban_colunas():
    if not KanbanColuna.objects.exists():
        defaults = [
            {"chave": "nao_iniciado", "titulo": "Não Iniciado", "cor": "#94a3b8", "ordem": 0},
            {"chave": "em_andamento", "titulo": "Em Andamento", "cor": "#3b82f6", "ordem": 1},
            {"chave": "concluido",    "titulo": "Concluído",    "cor": "#10b981", "ordem": 2},
        ]
        for d in defaults:
            KanbanColuna.objects.create(**d)

    if not KanbanCard.objects.exists():
        for p in MOCK_PROJETOS:
            chave = p.get("coluna_key") or p.get("status") or "nao_iniciado"
            coluna = KanbanColuna.objects.filter(chave=chave).first() \
                     or KanbanColuna.objects.order_by("ordem").first()
            prazo = None
            prazo_str = p.get("prazo", "")
            if prazo_str:
                try:
                    prazo = date_type.fromisoformat(prazo_str)
                except ValueError as e:
                    logger.debug("Prazo inválido em seed: %s — %s", prazo_str, e)
            KanbanCard.objects.create(
                coluna=coluna,
                titulo=p["titulo"],
                responsavel=p.get("responsavel", ""),
                area=p.get("area", ""),
                percentual=float(p.get("percentual", 0)),
                prazo=prazo,
                cor=p.get("cor", "gray"),
            )


@login_required
@tier_required("suporte", "admin")
def projetos_kanban(request, quadro_id=None):
    from django.db.models import Prefetch as _Prefetch
    quadros = Quadro.objects.filter(
        db_models.Q(criado_por=request.user) | db_models.Q(membros=request.user)
    ).distinct()

    if quadro_id:
        quadro = get_object_or_404(quadros, pk=quadro_id)
    else:
        quadro = quadros.first()
        if not quadro:
            quadro = Quadro.objects.create(nome="Organização dos Projetos", criado_por=request.user)
            for nome, cor, pos in [
                ("Não Iniciado", "#94a3b8", 0),
                ("Em Andamento", "#2563eb", 1),
                ("Concluído",    "#16a34a", 2),
                ("Bloqueado",    "#ea580c", 3),
            ]:
                Lista.objects.create(quadro=quadro, nome=nome, cor=cor, posicao=pos)

    cartoes_qs = (
        Cartao.objects
        .prefetch_related("etiquetas", "membros", "checklists__itens")
        .annotate(
            cl_total=db_models.Count("checklists__itens", distinct=True),
            cl_feitos=db_models.Count(
                "checklists__itens",
                filter=db_models.Q(checklists__itens__concluido=True),
                distinct=True,
            ),
        )
        .order_by("posicao", "id")
    )
    listas = quadro.listas.prefetch_related(
        _Prefetch("cartoes", queryset=cartoes_qs)
    ).order_by("posicao", "id")

    qs_todos = Chamado.objects.select_related("aberto_por", "agente").exclude(status__in=["resolvido", "fechado"])
    qs_meus  = qs_todos.filter(agente=request.user)

    return render(request, "projetos/kanban.html", {
        "quadro":        quadro,
        "listas":        listas,
        "todos_quadros": quadros.order_by("nome"),
        "etiquetas":     quadro.etiquetas.all(),
        "usuarios":      User.objects.filter(groups__name__in=["admin", "suporte"]).distinct().order_by("username"),
        "contagens":     _contagens_abertas(qs_todos),
        "meus_contagens": _contagens_abertas(qs_meus),
    })


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_coluna_criar(request):
    _seed_kanban_colunas()
    titulo = (request.POST.get("titulo") or "Nova Coluna").strip()
    cor = request.POST.get("cor") or "#94a3b8"
    max_ordem = KanbanColuna.objects.aggregate(m=db_models.Max("ordem"))["m"] or 0
    chave = f"col_{int(time.time() * 1000)}"
    col = KanbanColuna.objects.create(titulo=titulo, cor=cor, ordem=max_ordem + 1, chave=chave)
    return JsonResponse({"ok": True, "id": col.pk, "chave": col.chave, "titulo": col.titulo, "cor": col.cor})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_coluna_editar(request, pk):
    col = get_object_or_404(KanbanColuna, pk=pk)
    if "titulo" in request.POST:
        col.titulo = request.POST["titulo"].strip() or col.titulo
    if "cor" in request.POST:
        col.cor = request.POST["cor"]
    col.save()
    return JsonResponse({"ok": True})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_coluna_excluir(request, pk):
    col = get_object_or_404(KanbanColuna, pk=pk)
    first = KanbanColuna.objects.exclude(pk=pk).order_by("ordem").first()
    if first:
        KanbanCard.objects.filter(coluna=col).update(coluna=first)
    col.delete()
    return JsonResponse({"ok": True})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_colunas_reordenar(request):
    try:
        data = json.loads(request.body)
    except (ValueError, KeyError) as e:
        logger.warning("Payload inválido em kanban_colunas_reordenar: %s", e)
        return JsonResponse({"ok": False}, status=400)
    for i, chave in enumerate(data.get("order", [])):
        KanbanColuna.objects.filter(chave=chave).update(ordem=i)
    return JsonResponse({"ok": True})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_card_criar(request):
    coluna_key = (request.POST.get("coluna_key") or "").strip()
    if not coluna_key:
        return JsonResponse({"ok": False, "error": "coluna_key required"}, status=400)
    coluna = KanbanColuna.objects.filter(chave=coluna_key).first()
    if not coluna:
        return JsonResponse({"ok": False, "error": "coluna not found"}, status=404)
    titulo      = (request.POST.get("titulo")      or "Novo Card").strip()
    responsavel = (request.POST.get("responsavel") or "").strip()
    area        = (request.POST.get("area")        or "").strip()
    prazo_str   = (request.POST.get("prazo")       or "").strip()
    cor         = (request.POST.get("cor")         or "gray").strip()
    prazo = None
    if prazo_str:
        try:
            prazo = date_type.fromisoformat(prazo_str)
        except ValueError as e:
            logger.debug("Prazo inválido em kanban_card_criar: %s — %s", prazo_str, e)
    card = KanbanCard.objects.create(
        coluna=coluna, titulo=titulo, responsavel=responsavel,
        area=area, prazo=prazo, cor=cor, percentual=0.0,
    )
    return JsonResponse({"ok": True, "id": card.pk, "titulo": titulo,
                         "responsavel": responsavel, "area": area,
                         "prazo": prazo_str, "cor": cor, "percentual": 0.0})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_card_mover(request, pk):
    card = get_object_or_404(KanbanCard, pk=pk)
    coluna_key = (request.POST.get("coluna_key") or "").strip()
    if not coluna_key:
        return JsonResponse({"ok": False, "error": "coluna_key required"}, status=400)
    coluna_destino = KanbanColuna.objects.filter(chave=coluna_key).first()
    if coluna_destino is None:
        return JsonResponse({"ok": False, "error": "coluna not found"}, status=404)

    coluna_origem_chave = card.coluna.chave if card.coluna else ""
    if coluna_origem_chave == coluna_destino.chave:
        return JsonResponse({"ok": True, "noop": True})

    card.coluna = coluna_destino
    card.save(update_fields=["coluna"])
    logger.info(
        "Card #%s movido %s→%s por user=%s",
        card.pk, coluna_origem_chave, coluna_destino.chave, request.user.username,
    )
    KanbanAuditLog.objects.create(
        card=card,
        usuario=request.user,
        coluna_de=coluna_origem_chave,
        coluna_para=coluna_destino.chave,
    )
    return JsonResponse({"ok": True})


@login_required
@tier_required("suporte", "admin")
def projetos_indicadores(request):
    _seed_kanban_colunas()
    cards = KanbanCard.objects.select_related("coluna").all()
    total = cards.count()

    concluidos   = cards.filter(coluna__chave="concluido").count()
    em_andamento = cards.filter(coluna__chave="em_andamento").count()
    nao_iniciados = cards.filter(coluna__chave="nao_iniciado").count()
    atrasados = sum(1 for c in cards if c.atrasado)
    no_prazo  = max(em_andamento - atrasados, 0)
    pct_concluido = round(concluidos / total * 100, 1) if total else 0.0

    kpis = {
        "total": total, "concluidos": concluidos, "em_andamento": em_andamento,
        "nao_iniciados": nao_iniciados, "atrasados": atrasados,
        "no_prazo": no_prazo, "pct_concluido": pct_concluido,
    }

    concl_segments = [
        {"label": "Concluídos", "pct": pct_concluido, "color": "#10b981"},
        {"label": "Demais",     "pct": round(100 - pct_concluido, 1), "color": "#e5e7eb"},
    ]

    color_map = {"nao_iniciado": "#94a3b8", "em_andamento": "#60a5fa", "concluido": "#10b981"}
    status_segs = []
    for col in KanbanColuna.objects.annotate(count=db_models.Count("cards")):
        if col.count:
            pct = round(col.count / total * 100, 1) if total else 0.0
            status_segs.append({"label": col.titulo, "count": col.count, "pct": pct,
                                 "color": color_map.get(col.chave, "#a78bfa")})

    resp_qs = cards.values("responsavel").annotate(
        total=db_models.Count("id"),
        concl=db_models.Count("id", filter=db_models.Q(coluna__chave="concluido")),
    ).order_by("-total")
    por_resp = [
        {"resp": r["responsavel"], "total": r["total"], "concl": r["concl"],
         "pct": round(r["concl"] / r["total"] * 100, 1) if r["total"] else 0.0}
        for r in resp_qs if r["responsavel"]
    ]
    por_resp.sort(key=lambda x: (-x["pct"], x["resp"]))

    area_qs = cards.values("area").annotate(
        total=db_models.Count("id"),
        anda=db_models.Count("id", filter=db_models.Q(coluna__chave="em_andamento")),
        concl=db_models.Count("id", filter=db_models.Q(coluna__chave="concluido")),
    ).order_by("-total")
    por_area = [
        {"area": a["area"], "total": a["total"], "anda": a["anda"], "concl": a["concl"],
         "pct": round(a["total"] / total * 100, 1) if total else 0.0}
        for a in area_qs if a["area"]
    ]

    return render(request, "projetos/indicadores.html", {
        "kpis": kpis,
        "status_segments": status_segs, "status_total": total,
        "concl_segments": concl_segments,
        "por_resp": por_resp,
        "por_area": por_area,
    })


@login_required
@tier_required("suporte", "admin")
def card_editar(request, pk):
    card = get_object_or_404(KanbanCard, pk=pk)

    if request.method == "POST":
        card.titulo      = request.POST.get("titulo", card.titulo)
        card.responsavel = request.POST.get("responsavel", card.responsavel)
        card.area        = request.POST.get("area", card.area)
        card.cor         = request.POST.get("cor", card.cor)
        coluna_key = request.POST.get("status", "")
        if coluna_key:
            coluna = KanbanColuna.objects.filter(chave=coluna_key).first()
            if coluna:
                card.coluna = coluna
        prazo_raw = request.POST.get("prazo", "")
        card.prazo = date_type.fromisoformat(prazo_raw) if prazo_raw else None
        percentual_raw = request.POST.get("percentual", "")
        if percentual_raw:
            try:
                card.percentual = float(percentual_raw.replace(",", "."))
            except ValueError as e:
                logger.debug("Percentual inválido em card_editar pk=%s: %s — %s", pk, percentual_raw, e)
        card.save()
        return redirect("core:projetos_kanban")

    return render(request, "projetos/card_editar.html", {
        "projeto": {
            "id": card.pk, "titulo": card.titulo, "responsavel": card.responsavel,
            "area": card.area, "status": card.status, "percentual": card.percentual,
            "prazo": card.prazo.strftime("%Y-%m-%d") if card.prazo else "",
            "cor": card.cor,
        }
    })


# ============================================================
# COLABORADOR + SUPORTE + ADMIN
# ============================================================

def _abrir_chamado(request, template_name):
    is_privileged = request.user.is_superuser or request.user.groups.filter(
        name__in=["admin", "suporte"]
    ).exists()
    if request.method == "POST":
        form = AbrirChamadoForm(request.POST)
        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.aberto_por = request.user
            if not is_privileged:
                chamado.prioridade = "baixa"
            chamado.save()
            messages.success(request, f"Chamado #{chamado.pk} aberto com sucesso.")
            return redirect("core:meus_chamados")
    else:
        form = AbrirChamadoForm()
    return render(request, template_name, {"form": form, "is_privileged": is_privileged})


@login_required
@tier_required("colaborador", "suporte", "admin")
def chamado_novo(request):
    depts, topicos_json = _build_dept_context()
    meus_ativos = list(
        Ativo.objects.filter(custodiantes__usuario=request.user).order_by("patrimonio")
    )

    if request.method == "POST":
        assunto   = (request.POST.get("assunto")      or "").strip()
        descricao = (request.POST.get("descricao")    or "").strip()
        dept_id   = (request.POST.get("departamento") or "").strip()
        topico_id = (request.POST.get("topico")       or "").strip()
        ativo_id  = (request.POST.get("ativo")        or "").strip()

        erros = []
        if not assunto:   erros.append("Assunto é obrigatório.")
        if not dept_id:   erros.append("Departamento é obrigatório.")
        if not topico_id: erros.append("Tópico é obrigatório.")
        if not descricao: erros.append("Descrição é obrigatória.")

        if erros:
            for e in erros:
                messages.error(request, e)
        else:
            chamado = Chamado(
                assunto=assunto[:120],
                descricao=descricao,
                origem="portal",
                prioridade="baixa",
                aberto_por=request.user,
                sla_horas=72,
            )
            try:
                chamado.departamento_id = int(dept_id)
                chamado.topico_id = int(topico_id)
            except (ValueError, TypeError):
                pass
            if ativo_id:
                try:
                    chamado.ativo_id = int(ativo_id)
                except (ValueError, TypeError):
                    pass
            chamado.save()

            for arquivo in request.FILES.getlist("anexos"):
                anexo = AnexoChamado(chamado=chamado, enviado_por=request.user, arquivo=arquivo)
                try:
                    anexo.full_clean()
                    anexo.save()
                except Exception:
                    pass

            messages.success(
                request,
                f"Chamado #{chamado.pk} aberto com sucesso! "
                "Em breve nossa equipe entrará em contato. "
                "Você pode acompanhar em 'Meus Chamados'."
            )
            return redirect("core:meus_chamados")

    return render(request, "chamados/novo_usuario.html", {
        "departamentos": depts,
        "topicos_json":  json.dumps(topicos_json),
        "meus_ativos":   meus_ativos,
        "user_nome": request.user.get_full_name() or request.user.username,
    })


@login_required
def ativos_meus(request):
    ativos = list(
        Ativo.objects.filter(custodiantes__usuario=request.user)
        .values("id", "patrimonio", "modelo", "categoria")
        .order_by("patrimonio")
    )
    return JsonResponse({"results": ativos})


def _is_admin(user):
    return user.is_superuser or user.groups.filter(name__iexact="admin").exists()


_SLA_POR_PRIORIDADE = {"baixa": 72, "media": 24, "alta": 8, "critica": 2}


def _build_dept_context():
    depts = list(
        Departamento.objects.filter(ativo=True)
        .prefetch_related("topicos")
        .order_by("nome")
    )
    topicos_json = {
        str(d.pk): [
            {"id": t.pk, "nome": t.nome}
            for t in d.topicos.filter(ativo=True).order_by("nome")
        ]
        for d in depts
    }
    return depts, topicos_json


@login_required
@tier_required("suporte", "admin")
def colaborador_buscar(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})
    qs = (
        Funcionario.objects
        .select_related("usuario", "ativo_atribuido")
        .filter(ativo=True, usuario__isnull=False)
        .filter(
            db_models.Q(nome__icontains=q)
            | db_models.Q(email__icontains=q)
            | db_models.Q(ramal__icontains=q)
            | db_models.Q(usuario__username__icontains=q)
        )[:8]
    )
    results = []
    for f in qs:
        ativos = []
        if f.ativo_atribuido:
            ativos.append({
                "id": f.ativo_atribuido.pk,
                "patrimonio": f.ativo_atribuido.patrimonio,
                "modelo": f.ativo_atribuido.modelo or "",
                "categoria": f.ativo_atribuido.categoria or "",
            })
        results.append({
            "user_id":       f.usuario_id,
            "funcionario_id": f.pk,
            "nome":     f.nome,
            "email":    f.email,
            "username": f.usuario.username if f.usuario else "",
            "setor":    f.setor,
            "funcao":   f.funcao,
            "ramal":    f.ramal,
            "contato":  f.contato,
            "ativos":   ativos,
        })
    return JsonResponse({"results": results})


@login_required
@tier_required("colaborador", "suporte", "admin")
def chamado_criar_tier(request):
    depts, topicos_json = _build_dept_context()
    is_admin = _is_admin(request.user)

    if request.method == "POST":
        assunto        = (request.POST.get("assunto")       or "").strip()
        origem         = (request.POST.get("origem")        or "portal").strip()
        prioridade     = (request.POST.get("prioridade")    or "baixa").strip()
        descricao      = (request.POST.get("descricao")     or "").strip()
        dept_id        = (request.POST.get("departamento")  or "").strip()
        topico_id      = (request.POST.get("topico")        or "").strip()
        ativo_id       = (request.POST.get("ativo")         or "").strip()
        solicitante_id = (request.POST.get("solicitante_id") or "").strip()

        valid_origens     = [o[0] for o in Chamado.ORIGENS]
        valid_prioridades = [p[0] for p in Chamado.PRIORIDADES]
        if origem not in valid_origens:         origem = "portal"
        if prioridade not in valid_prioridades: prioridade = "baixa"

        erros = []
        if not assunto:   erros.append("Assunto é obrigatório.")
        if not dept_id:   erros.append("Departamento é obrigatório.")
        if not topico_id: erros.append("Tópico é obrigatório.")
        if not descricao: erros.append("Descrição é obrigatória.")
        if is_admin and not solicitante_id:
            erros.append("Selecione o colaborador solicitante.")

        if erros:
            for e in erros:
                messages.error(request, e)
        else:
            aberto_por = request.user
            if is_admin and solicitante_id:
                try:
                    aberto_por = User.objects.get(pk=int(solicitante_id))
                except (User.DoesNotExist, ValueError, TypeError):
                    aberto_por = request.user

            chamado = Chamado(
                assunto=assunto[:120],
                descricao=descricao,
                origem=origem,
                prioridade=prioridade,
                aberto_por=aberto_por,
                sla_horas=_SLA_POR_PRIORIDADE.get(prioridade, 72),
            )
            try:
                chamado.departamento_id = int(dept_id)
                chamado.topico_id = int(topico_id)
            except (ValueError, TypeError):
                messages.error(request, "Departamento ou tópico inválido.")
                chamado.departamento_id = None
                chamado.topico_id = None
            if ativo_id:
                try:
                    chamado.ativo_id = int(ativo_id)
                except (ValueError, TypeError):
                    pass
            chamado.save()

            for arquivo in request.FILES.getlist("anexos"):
                anexo = AnexoChamado(
                    chamado=chamado, enviado_por=request.user, arquivo=arquivo
                )
                try:
                    anexo.full_clean()
                    anexo.save()
                except Exception:
                    pass

            messages.success(request, f"Chamado #{chamado.pk} aberto com sucesso.")
            return redirect("core:chamado_detalhe", cid=chamado.pk)

    ativos_recentes = list(Ativo.objects.order_by("-id")[:4])
    return render(request, "chamados/abrir_tier.html", {
        "departamentos":   depts,
        "topicos_json":    json.dumps(topicos_json),
        "ativos_recentes": ativos_recentes,
        "user_nome": request.user.get_full_name() or request.user.username,
        "is_admin":  is_admin,
    })


def _sla_vencidos_count(qs):
    agora = timezone.now()
    vencidos = 0
    for c in qs.filter(status__in=["aberto", "em_atendimento"]).values("aberto_em", "sla_horas"):
        if c["aberto_em"] + timedelta(hours=(c["sla_horas"] or 8)) < agora:
            vencidos += 1
    return vencidos


def _contagens_abertas(qs):
    agora = timezone.now()
    return {
        "aberto":    qs.filter(status="aberto").count(),
        "respondido": qs.filter(status="em_atendimento").count(),
        "vencido":   _sla_vencidos_count(qs),
    }


def _contagens_fechadas():
    hoje = timezone.localdate()
    qs = Chamado.objects.filter(status__in=["resolvido", "fechado"])
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes    = hoje.replace(day=1)
    inicio_tri    = hoje.replace(month=((hoje.month - 1) // 3) * 3 + 1, day=1)
    return {
        "hoje":      qs.filter(fechado_em__date=hoje).count(),
        "ontem":     qs.filter(fechado_em__date=hoje - timedelta(days=1)).count(),
        "semana":    qs.filter(fechado_em__date__gte=inicio_semana).count(),
        "mes":       qs.filter(fechado_em__date__gte=inicio_mes).count(),
        "trimestre": qs.filter(fechado_em__date__gte=inicio_tri).count(),
        "ano":       qs.filter(fechado_em__date__gte=hoje.replace(month=1, day=1)).count(),
    }


def _lista_contexto(request, qs, titulo, aba, ordem_default="-atualizado_em"):
    q         = (request.GET.get("q") or "").strip()
    ordem     = request.GET.get("ordem", "atualizado_em")
    dir_ordem = request.GET.get("dir", "desc")

    # Filtros da barra (acumulativos, via GET)
    status_sel      = request.GET.get("status", "")
    fila_sel        = request.GET.get("fila", "")
    agente_sel      = request.GET.get("agente", "")
    solicitante_sel = request.GET.get("solicitante", "")

    if q:
        qs = qs.filter(
            db_models.Q(assunto__icontains=q)
            | db_models.Q(aberto_por__username__icontains=q)
            | db_models.Q(pk__icontains=q)
        )

    # Status: "vencido" é calculado por SLA; os demais batem com Chamado.STATUS
    if status_sel == "vencido":
        agora = timezone.now()
        vencidos = [
            c.pk
            for c in qs.filter(status__in=["aberto", "em_atendimento"]).only("aberto_em", "sla_horas")
            if c.aberto_em + timedelta(hours=(c.sla_horas or 8)) < agora
        ]
        qs = qs.filter(pk__in=vencidos)
    elif status_sel:
        qs = qs.filter(status=status_sel)

    if fila_sel.isdigit():
        qs = qs.filter(departamento_id=fila_sel)

    if agente_sel == "nenhum":
        qs = qs.filter(agente__isnull=True)
    elif agente_sel.isdigit():
        qs = qs.filter(agente_id=agente_sel)

    if solicitante_sel.isdigit():
        qs = qs.filter(aberto_por_id=solicitante_sel)

    campo = ordem if ordem in ["id", "atualizado_em", "prioridade", "aberto_em", "fechado_em"] else "atualizado_em"
    qs = qs.order_by(campo if dir_ordem == "asc" else f"-{campo}")
    qs = qs.annotate(total_respostas=db_models.Count(
        "historico", filter=db_models.Q(historico__tipo="comentario")
    ))

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get("page", 1))

    qs_todos = Chamado.objects.select_related("aberto_por", "agente").exclude(status__in=["resolvido", "fechado"])
    qs_meus  = qs_todos.filter(agente=request.user)

    return {
        "page_obj":           page_obj,
        "titulo_aba":         titulo,
        "aba_ativa":          aba,
        "contagens":          _contagens_abertas(qs_todos),
        "meus_contagens":     _contagens_abertas(qs_meus),
        "fechados_contagens": _contagens_fechadas(),
        "ordem":              campo,
        "dir":                dir_ordem,
        "q":                  q,
        # Listas para os dropdowns da barra de filtros
        "filas": (Departamento.objects
                  .annotate(total=db_models.Count("chamados"))
                  .filter(total__gt=0)
                  .order_by("nome")),
        "agentes": (User.objects
                    .filter(chamados_atribuidos__isnull=False)
                    .distinct()
                    .order_by("first_name", "username")),
        "solicitantes": (User.objects
                         .filter(chamados_abertos__isnull=False)
                         .distinct()
                         .order_by("first_name", "username")),
        # Valores selecionados (marcam a opção ativa e o label do botão)
        "status_sel":      status_sel,
        "fila_sel":        fila_sel,
        "agente_sel":      agente_sel,
        "solicitante_sel": solicitante_sel,
    }


@login_required
@tier_required("suporte", "admin")
def chamados_todos(request):
    qs = Chamado.objects.select_related("aberto_por", "agente") \
                        .exclude(status__in=["resolvido", "fechado"])
    ctx = _lista_contexto(request, qs, "Abertos", "abertos")
    return render(request, "chamados/todos.html", ctx)


@login_required
@tier_required("suporte", "admin")
def chamados_todos_meus(request):
    qs = Chamado.objects.select_related("aberto_por", "agente") \
                        .filter(agente=request.user) \
                        .exclude(status__in=["resolvido", "fechado"])
    ctx = _lista_contexto(request, qs, "Meus Tickets", "meus")
    return render(request, "chamados/todos.html", ctx)


@login_required
@tier_required("suporte", "admin")
def chamados_todos_fechados(request):
    hoje = timezone.localdate()
    periodo = request.GET.get("periodo", "mes")
    datas = {
        "hoje":      hoje,
        "ontem":     hoje - timedelta(days=1),
        "semana":    hoje - timedelta(days=hoje.weekday()),
        "mes":       hoje.replace(day=1),
        "trimestre": hoje.replace(month=((hoje.month - 1) // 3) * 3 + 1, day=1),
        "ano":       hoje.replace(month=1, day=1),
    }
    inicio = datas.get(periodo, datas["mes"])
    qs = Chamado.objects.select_related("aberto_por", "agente") \
                        .filter(status__in=["resolvido", "fechado"],
                                fechado_em__date__gte=inicio)
    ctx = _lista_contexto(request, qs, "Fechados", "fechados", ordem_default="-fechado_em")
    ctx["periodo"] = periodo
    return render(request, "chamados/todos.html", ctx)


@login_required
@tier_required("suporte", "admin")
@require_POST
def chamado_acao_massa(request):
    ids  = [i for i in (request.POST.get("ids") or "").split(",") if i.isdigit()]
    acao = request.POST.get("acao", "")
    qs   = Chamado.objects.filter(pk__in=ids)

    if acao == "excluir":
        qs.delete()
        messages.success(request, f"{len(ids)} chamado(s) excluído(s).")
    elif acao == "atribuir":
        qs.update(agente=request.user)
        messages.success(request, f"{len(ids)} chamado(s) atribuído(s) a você.")
    elif acao == "exportar":
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="chamados.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Assunto", "Status", "Prioridade", "Origem", "Aberto por", "Agente", "Abertura"])
        for c in qs.select_related("aberto_por", "agente"):
            writer.writerow([
                c.pk, c.assunto, c.status, c.prioridade, c.origem,
                c.aberto_por.username if c.aberto_por else "",
                c.agente.username if c.agente else "",
                c.aberto_em.strftime("%d/%m/%Y %H:%M"),
            ])
        return response

    return redirect("core:chamados_todos")


@login_required
@tier_required("colaborador", "suporte", "admin")
def meus_chamados(request):
    is_privileged = request.user.is_superuser or request.user.groups.filter(
        name__in=["admin", "suporte"]
    ).exists()

    qs = Chamado.objects.select_related("aberto_por", "agente")
    if not is_privileged:
        qs = qs.filter(aberto_por=request.user)

    ctx = _lista_contexto(request, qs, "Meus Chamados", "meus_chamados")
    ctx["is_privileged"] = is_privileged
    return render(request, "chamados/meus.html", ctx)


def _calcular_sla(chamado):
    prazo_horas = chamado.sla_horas or 8
    agora = timezone.now()
    vencimento = chamado.aberto_em + timedelta(hours=prazo_horas)
    decorridas = round((agora - chamado.aberto_em).total_seconds() / 3600, 1)
    restantes  = round(max((vencimento - agora).total_seconds() / 3600, 0), 1)
    return {
        "prazo_horas":         prazo_horas,
        "vencimento":          vencimento,
        "horas_decorridas":    decorridas,
        "horas_restantes":     restantes,
        "percentual_consumido": min(round(decorridas / prazo_horas * 100, 1), 100),
        "dentro_prazo":        agora <= vencimento,
    }


def _is_privileged(user):
    return user.is_superuser or user.groups.filter(name__in=["admin", "suporte"]).exists()


@login_required
@tier_required("colaborador", "suporte", "admin")
def chamado_detalhe(request, cid: int):
    chamado = get_object_or_404(
        Chamado.objects.select_related("aberto_por", "agente", "ativo")
                       .prefetch_related("historico__autor", "anexos__enviado_por"),
        pk=cid,
    )
    privileged = _is_privileged(request.user)
    if not privileged and chamado.aberto_por != request.user:
        messages.error(request, "Sem permissão para acessar este chamado.")
        return redirect("core:meus_chamados")

    responder_form = ResponderChamadoForm(initial={
        "novo_status": chamado.status,
        "prioridade":  chamado.prioridade,
        "agente":      chamado.agente_id,
    })

    return render(request, "chamados/detalhe.html", {
        "chamado":    chamado,
        "historico":  chamado.historico.select_related("autor").order_by("quando"),
        "sla":        _calcular_sla(chamado),
        "form":       responder_form,
        "pode_responder": privileged,
    })


@login_required
@tier_required("suporte", "admin")
@require_POST
def chamado_atualizar(request, cid: int):
    chamado = get_object_or_404(Chamado, pk=cid)
    form = ResponderChamadoForm(request.POST)
    if not form.is_valid():
        error_msgs = "; ".join(
            f"{field}: {', '.join(errs)}"
            for field, errs in form.errors.items()
        )
        messages.error(request, f"Dados inválidos: {error_msgs}")
        return redirect("core:chamado_detalhe", cid=chamado.pk)

    status_ant = chamado.status
    prio_ant   = chamado.prioridade
    agente_ant = chamado.agente_id

    agente = form.cleaned_data["agente"]  # User instance or None
    chamado.status     = form.cleaned_data["novo_status"]
    chamado.prioridade = form.cleaned_data["prioridade"]
    chamado.agente     = agente

    if chamado.status in ("resolvido", "fechado") and not chamado.fechado_em:
        chamado.fechado_em = timezone.now()
    elif chamado.status not in ("resolvido", "fechado"):
        chamado.fechado_em = None

    chamado.save()
    logger.info(
        "Chamado #%s atualizado por user=%s status=%s→%s",
        chamado.pk, request.user.username, status_ant, chamado.status,
    )
    comentario    = (form.cleaned_data.get("comentario") or "").strip()
    agente_id_new = agente.pk if agente else None

    if status_ant != chamado.status:
        HistoricoChamado.objects.create(
            chamado=chamado, autor=request.user,
            tipo="status", descricao="alterou o status para",
            valor_anterior=status_ant, valor_novo=chamado.status,
            texto=comentario,
        )

    if prio_ant != chamado.prioridade:
        HistoricoChamado.objects.create(
            chamado=chamado, autor=request.user,
            tipo="prioridade", descricao="alterou a prioridade para",
            valor_anterior=prio_ant, valor_novo=chamado.prioridade,
        )

    if agente_ant != agente_id_new:
        HistoricoChamado.objects.create(
            chamado=chamado, autor=request.user,
            tipo="atribuicao", descricao="atribuiu o chamado",
            texto=comentario,
        )

    if (comentario
            and status_ant == chamado.status
            and prio_ant == chamado.prioridade
            and agente_ant == agente_id_new):
        HistoricoChamado.objects.create(
            chamado=chamado, autor=request.user,
            tipo="comentario", descricao="adicionou um comentário",
            texto=comentario,
        )

    messages.success(request, "Chamado atualizado.")
    return redirect("core:chamado_detalhe", cid=chamado.pk)


@login_required
@tier_required("suporte", "admin")
@require_POST
def chamado_atribuir(request, cid: int):
    chamado = get_object_or_404(Chamado, pk=cid)
    chamado.agente = request.user
    chamado.save()
    HistoricoChamado.objects.create(
        chamado=chamado, autor=request.user,
        tipo="atribuicao", descricao="assumiu o chamado",
    )
    messages.success(request, "Chamado atribuído a você.")
    return redirect("core:chamado_detalhe", cid=chamado.pk)


@login_required
@tier_required("suporte", "admin")
@require_POST
def chamado_fechar(request, cid: int):
    chamado = get_object_or_404(Chamado, pk=cid)
    chamado.status = "resolvido"
    chamado.fechado_em = timezone.now()
    chamado.save()
    HistoricoChamado.objects.create(
        chamado=chamado, autor=request.user,
        tipo="status", descricao="fechou o chamado",
        valor_novo="resolvido",
    )
    messages.success(request, "Chamado fechado.")
    return redirect("core:chamado_detalhe", cid=chamado.pk)


@login_required
@tier_required("suporte", "admin")
@require_POST
def chamado_anexar(request, cid: int):
    chamado = get_object_or_404(Chamado, pk=cid)
    arquivo = request.FILES.get("arquivo")
    if not arquivo:
        messages.error(request, "Nenhum arquivo selecionado.")
        return redirect("core:chamado_detalhe", cid=chamado.pk)

    anexo = AnexoChamado(chamado=chamado, enviado_por=request.user, arquivo=arquivo)
    try:
        anexo.full_clean()
        anexo.save()
        logger.info("Anexo adicionado em chamado=#%s por user=%s", cid, request.user.username)
        messages.success(request, "Anexo adicionado.")
    except ValidationError as e:
        erros = "; ".join(e.messages)
        messages.error(request, f"Anexo rejeitado: {erros}")
    return redirect("core:chamado_detalhe", cid=chamado.pk)


# ============================================================
# COLABORADOR ONLY
# ============================================================

# ============================================================
# KANBAN RICO — endpoints AJAX
# ============================================================

@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_quadro_criar(request):
    nome = (request.POST.get("nome") or "").strip()
    if not nome:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest("nome obrigatório")
    quadro = Quadro.objects.create(nome=nome, criado_por=request.user)
    for n, cor, pos in [
        ("Não Iniciado", "#94a3b8", 0),
        ("Em Andamento", "#2563eb", 1),
        ("Concluído",    "#16a34a", 2),
    ]:
        Lista.objects.create(quadro=quadro, nome=n, cor=cor, posicao=pos)
    from django.urls import reverse
    return redirect(reverse("core:projetos_kanban_quadro", args=[quadro.pk]))


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_cartao_criar(request):
    lista = get_object_or_404(Lista, pk=request.POST.get("lista_id"))
    titulo = (request.POST.get("titulo") or "").strip()
    if not titulo:
        return JsonResponse({"ok": False}, status=400)
    pos = lista.cartoes.count()
    c = Cartao.objects.create(lista=lista, titulo=titulo, posicao=pos, criado_por=request.user)
    return JsonResponse({"ok": True, "id": c.pk, "titulo": c.titulo})


@login_required
@tier_required("suporte", "admin")
def kanban_cartao_detail(request, pk):
    from django.db.models import Prefetch as _Prefetch
    cartao = get_object_or_404(
        Cartao.objects
            .select_related("lista")
            .prefetch_related(
                "etiquetas",
                "membros",
                _Prefetch(
                    "checklists",
                    queryset=ChecklistKanban.objects.order_by("posicao").prefetch_related(
                        _Prefetch("itens", queryset=ItemChecklistKanban.objects.order_by("posicao"))
                    ),
                ),
                _Prefetch(
                    "atividades",
                    queryset=AtividadeCartao.objects.select_related("autor").order_by("-criado_em"),
                ),
            ),
        pk=pk,
    )
    checklists_data = [
        {
            "id": cl.pk,
            "titulo": cl.titulo,
            "itens": [
                {"id": it.pk, "texto": it.texto, "concluido": it.concluido}
                for it in cl.itens.all()
            ],
        }
        for cl in cartao.checklists.all()
    ]
    atividades_data = [
        {
            "tipo":      at.tipo,
            "autor":     (at.autor.get_full_name() or at.autor.username) if at.autor else "Sistema",
            "texto":     at.texto,
            "criado_em": at.criado_em.strftime("%d/%m %H:%M"),
        }
        for at in cartao.atividades.all()[:40]
    ]
    return JsonResponse({
        "id":           cartao.pk,
        "titulo":       cartao.titulo,
        "descricao":    cartao.descricao,
        "progresso":    cartao.progresso,
        "concluido":    cartao.concluido,
        "area":         cartao.area,
        "capa_cor":     cartao.capa_cor,
        "data_inicio":  cartao.data_inicio.isoformat()            if cartao.data_inicio  else "",
        "data_entrega": cartao.data_entrega.date().isoformat()    if cartao.data_entrega else "",
        "lista_id":     cartao.lista_id,
        "lista_nome":   cartao.lista.nome,
        "lista_cor":    cartao.lista.cor,
        "etiquetas":    [{"id": e.pk, "nome": e.nome, "cor": e.cor} for e in cartao.etiquetas.all()],
        "membros":      [{"id": u.pk, "display": u.get_full_name() or u.username} for u in cartao.membros.all()],
        "checklists":   checklists_data,
        "atividades":   atividades_data,
    })


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_cartao_atualizar(request, pk):
    cartao = get_object_or_404(Cartao, pk=pk)
    for field in ("titulo", "descricao", "area", "capa_cor"):
        if field in request.POST:
            setattr(cartao, field, request.POST[field])
    if "progresso" in request.POST:
        cartao.progresso = int(request.POST["progresso"])
    if "concluido" in request.POST:
        cartao.concluido = request.POST["concluido"] in ("1", "true", "on")
    if "data_inicio" in request.POST:
        cartao.data_inicio = request.POST["data_inicio"] or None
    if "data_entrega" in request.POST:
        cartao.data_entrega = _parse_dt_aware(request.POST["data_entrega"])
    cartao.save()
    return JsonResponse({"ok": True})


def _parse_dt_aware(raw):
    """Converte 'YYYY-MM-DD' ou 'YYYY-MM-DDTHH:MM' em datetime timezone-aware (ou None)."""
    raw = (raw or "").strip()
    if not raw:
        return None
    from datetime import datetime, time
    from django.utils import timezone
    from django.utils.dateparse import parse_datetime, parse_date
    dt = parse_datetime(raw)
    if dt is None:
        d = parse_date(raw)
        dt = datetime.combine(d, time.min) if d else None
    if dt is not None and timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_cartao_mover(request, pk):
    cartao = get_object_or_404(Cartao, pk=pk)
    nova_lista = get_object_or_404(Lista, pk=request.POST.get("lista_id"))
    cartao.lista = nova_lista
    cartao.posicao = int(request.POST.get("posicao", 0))
    cartao.save()
    AtividadeCartao.objects.create(
        cartao=cartao, autor=request.user, tipo="atividade",
        texto=f'moveu este cartão para "{nova_lista.nome}".',
    )
    return JsonResponse({"ok": True})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_cartao_excluir(request, pk):
    Cartao.objects.filter(pk=pk).delete()
    return JsonResponse({"ok": True})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_cartao_etiqueta(request, pk):
    cartao = get_object_or_404(Cartao, pk=pk)
    etq = get_object_or_404(Etiqueta, pk=request.POST.get("etiqueta_id"))
    if cartao.etiquetas.filter(pk=etq.pk).exists():
        cartao.etiquetas.remove(etq)
        return JsonResponse({"ok": True, "acao": "removida"})
    cartao.etiquetas.add(etq)
    return JsonResponse({"ok": True, "acao": "adicionada"})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_cartao_membro(request, pk):
    cartao = get_object_or_404(Cartao, pk=pk)
    user = get_object_or_404(User, pk=request.POST.get("user_id"))
    if cartao.membros.filter(pk=user.pk).exists():
        cartao.membros.remove(user)
        return JsonResponse({"ok": True, "acao": "removido"})
    cartao.membros.add(user)
    return JsonResponse({"ok": True, "acao": "adicionado"})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_cartao_comentar(request, pk):
    cartao = get_object_or_404(Cartao, pk=pk)
    texto = (request.POST.get("texto") or "").strip()
    if not texto:
        return JsonResponse({"ok": False}, status=400)
    AtividadeCartao.objects.create(cartao=cartao, autor=request.user, tipo="comentario", texto=texto)
    return JsonResponse({"ok": True})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_checklist_criar(request, pk):
    cartao = get_object_or_404(Cartao, pk=pk)
    titulo = (request.POST.get("titulo") or "Checklist").strip()
    cl = ChecklistKanban.objects.create(cartao=cartao, titulo=titulo, posicao=cartao.checklists.count())
    return JsonResponse({"ok": True, "id": cl.pk, "titulo": cl.titulo})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_checklist_excluir(request, pk):
    ChecklistKanban.objects.filter(pk=pk).delete()
    return JsonResponse({"ok": True})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_checklist_item_criar(request, pk):
    cl = get_object_or_404(ChecklistKanban, pk=pk)
    texto = (request.POST.get("texto") or "").strip()
    if not texto:
        return JsonResponse({"ok": False}, status=400)
    item = ItemChecklistKanban.objects.create(checklist=cl, texto=texto, posicao=cl.itens.count())
    return JsonResponse({"ok": True, "id": item.pk})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_item_toggle(request, pk):
    item = get_object_or_404(ItemChecklistKanban, pk=pk)
    item.concluido = not item.concluido
    item.save()
    return JsonResponse({"ok": True, "concluido": item.concluido})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_item_excluir(request, pk):
    ItemChecklistKanban.objects.filter(pk=pk).delete()
    return JsonResponse({"ok": True})


@login_required
@tier_required("suporte", "admin")
@require_POST
def kanban_lista_criar(request, quadro_id):
    quadro = get_object_or_404(Quadro, pk=quadro_id)
    nome = (request.POST.get("nome") or "").strip()
    if not nome:
        return JsonResponse({"ok": False}, status=400)
    lista = Lista.objects.create(
        quadro=quadro, nome=nome,
        cor=request.POST.get("cor", "#6b7280"),
        posicao=quadro.listas.count(),
    )
    return JsonResponse({"ok": True, "id": lista.pk, "nome": lista.nome})


# ============================================================
# COLABORADOR ONLY

@login_required
@tier_required("colaborador")
def assistente(request):
    user = request.user
    try:
        full_name = user.funcionario.nome
    except Exception:
        full_name = user.get_full_name() or user.username
    parts = full_name.split()
    first_name = parts[0] if parts else user.username
    initials = "".join(p[0].upper() for p in parts[:2]) or user.username[:2].upper()
    return render(request, "chat/assistente.html", {
        "first_name": first_name,
        "user_initials": initials,
    })


@login_required
@tier_required("colaborador")
@require_POST
def assistente_responder(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "JSON inválido"}, status=400)

    # Limpa histórico ao iniciar nova conversa
    if data.get("action") == "clear":
        request.session.pop("chat_history", None)
        return JsonResponse({"ok": True})

    user_text = data.get("text", "").strip()
    if not user_text:
        return JsonResponse({"error": "Texto vazio"}, status=400)

    from django.conf import settings as django_settings
    api_key = getattr(django_settings, "GEMINI_API_KEY", "")
    if not api_key:
        return JsonResponse({
            "html": "<p>O assistente de IA não está configurado. Configure a variável <code>GEMINI_API_KEY</code> no arquivo <code>.env</code>.</p>",
            "chips": [],
        })

    try:
        from google import genai
        from google.genai import types as genai_types

        client = genai.Client(api_key=api_key)

        # Reconstrói histórico como objetos Content
        history = request.session.get("chat_history", [])
        contents = [
            genai_types.Content(role=msg["role"], parts=[genai_types.Part(text=msg["parts"][0])])
            for msg in history
        ]
        contents.append(genai_types.Content(role="user", parts=[genai_types.Part(text=user_text)]))

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=montar_system_prompt(request),
                max_output_tokens=800,
            ),
        )
        reply_html = response.text

        history.append({"role": "user", "parts": [user_text]})
        history.append({"role": "model", "parts": [reply_html]})
        request.session["chat_history"] = history[-20:]

        return JsonResponse({"html": reply_html, "chips": []})

    except Exception as exc:
        logger.exception("Erro ao chamar Gemini API: %s", exc)
        return JsonResponse({
            "html": "<p>Não consegui me conectar ao serviço de IA no momento. Tente novamente em instantes.</p>",
            "chips": ["Tentar novamente"],
        })
