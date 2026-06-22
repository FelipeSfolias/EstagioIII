from django.db import models
from django.utils import timezone


# ── Kanban rico (Quadro / Lista / Cartao) ────────────────────

class Quadro(models.Model):
    nome = models.CharField(max_length=200)
    criado_por = models.ForeignKey(
        "auth.User", related_name="quadros_criados",
        on_delete=models.SET_NULL, null=True,
    )
    membros = models.ManyToManyField(
        "auth.User", related_name="quadros_membro", blank=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Lista(models.Model):
    quadro = models.ForeignKey(Quadro, related_name="listas", on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    cor = models.CharField(max_length=20, default="#6b7280")
    posicao = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["posicao", "id"]

    def __str__(self):
        return f"{self.quadro.nome} / {self.nome}"


class Etiqueta(models.Model):
    quadro = models.ForeignKey(Quadro, related_name="etiquetas", on_delete=models.CASCADE)
    nome = models.CharField(max_length=80)
    cor = models.CharField(max_length=20, default="#2563eb")

    def __str__(self):
        return self.nome


class Cartao(models.Model):
    lista = models.ForeignKey(Lista, related_name="cartoes", on_delete=models.CASCADE)
    titulo = models.CharField(max_length=300)
    descricao = models.TextField(blank=True)
    progresso = models.PositiveSmallIntegerField(default=0)
    posicao = models.PositiveIntegerField(default=0)
    area = models.CharField(max_length=100, blank=True)
    capa_cor = models.CharField(max_length=20, blank=True)
    concluido = models.BooleanField(default=False)
    data_inicio = models.DateField(null=True, blank=True)
    data_entrega = models.DateTimeField(null=True, blank=True)
    etiquetas = models.ManyToManyField(Etiqueta, related_name="cartoes", blank=True)
    membros = models.ManyToManyField(
        "auth.User", related_name="cartoes_kanban", blank=True,
    )
    criado_por = models.ForeignKey(
        "auth.User", related_name="cartoes_criados",
        on_delete=models.SET_NULL, null=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["posicao", "id"]

    def __str__(self):
        return self.titulo

    @property
    def atrasado(self):
        if self.data_entrega and not self.concluido:
            return self.data_entrega < timezone.now()
        return False


class ChecklistKanban(models.Model):
    cartao = models.ForeignKey(Cartao, related_name="checklists", on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200, default="Checklist")
    posicao = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["posicao", "id"]

    @property
    def pct(self):
        total = self.itens.count()
        return round(self.itens.filter(concluido=True).count() / total * 100) if total else 0


class ItemChecklistKanban(models.Model):
    checklist = models.ForeignKey(
        ChecklistKanban, related_name="itens", on_delete=models.CASCADE,
    )
    texto = models.CharField(max_length=500)
    concluido = models.BooleanField(default=False)
    posicao = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["posicao", "id"]


class AtividadeCartao(models.Model):
    TIPOS = [("atividade", "Atividade"), ("comentario", "Comentário")]
    cartao = models.ForeignKey(Cartao, related_name="atividades", on_delete=models.CASCADE)
    autor = models.ForeignKey(
        "auth.User", related_name="atividades_kanban",
        on_delete=models.SET_NULL, null=True,
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default="atividade")
    texto = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]


# ── Kanban simples (colunas + cards legado) ──────────────────

class KanbanColuna(models.Model):
    chave = models.CharField(max_length=60, unique=True)
    titulo = models.CharField(max_length=100)
    cor = models.CharField(max_length=20, default="#94a3b8")
    ordem = models.IntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordem"]
        verbose_name = "Coluna Kanban"
        verbose_name_plural = "Colunas Kanban"

    def __str__(self):
        return self.titulo


class KanbanCard(models.Model):
    coluna = models.ForeignKey(
        KanbanColuna, on_delete=models.CASCADE,
        related_name="cards", null=True, blank=True,
    )
    titulo      = models.CharField(max_length=200, verbose_name="Título")
    responsavel = models.CharField(max_length=100, blank=True, verbose_name="Responsável")
    area        = models.CharField(max_length=100, blank=True, verbose_name="Área")
    percentual  = models.FloatField(default=0.0, verbose_name="Progresso (%)")
    prazo       = models.DateField(null=True, blank=True, verbose_name="Prazo")
    cor         = models.CharField(max_length=20, default="gray", verbose_name="Cor")
    ordem       = models.PositiveIntegerField(default=0)
    criado_em   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordem", "criado_em"]
        verbose_name = "Card Kanban"
        verbose_name_plural = "Cards Kanban"

    def __str__(self):
        return self.titulo

    @property
    def atrasado(self):
        if self.prazo and self.coluna and self.coluna.chave != "concluido":
            return self.prazo < timezone.localdate()
        return False

    @property
    def status(self):
        return self.coluna.chave if self.coluna else ""


class KanbanAuditLog(models.Model):
    card = models.ForeignKey(KanbanCard, on_delete=models.CASCADE, related_name="audit_logs")
    usuario = models.ForeignKey(
        "auth.User", null=True, on_delete=models.SET_NULL, related_name="kanban_audits",
    )
    coluna_de   = models.CharField(max_length=60, blank=True)
    coluna_para = models.CharField(max_length=60)
    criado_em   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Log de Auditoria Kanban"
        verbose_name_plural = "Logs de Auditoria Kanban"

    def __str__(self):
        return f"{self.card_id}: {self.coluna_de} → {self.coluna_para} ({self.criado_em:%d/%m %H:%M})"
