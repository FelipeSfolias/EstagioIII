from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import User


def validar_tamanho_anexo(arquivo):
    limite_mb = 10
    if arquivo.size > limite_mb * 1024 * 1024:
        raise ValidationError(f"Arquivo excede o limite de {limite_mb} MB.")


class Chamado(models.Model):
    ORIGENS = [
        ("portal",     "Portal"),
        ("email",      "E-mail"),
        ("telefone",   "Telefone"),
        ("presencial", "Presencial"),
    ]
    PRIORIDADES = [
        ("baixa",   "Baixa"),
        ("media",   "Média"),
        ("alta",    "Alta"),
        ("critica", "Crítica"),
    ]
    STATUS = [
        ("aberto", "Aberto"),
        ("em_atendimento", "Em Atendimento"),
        ("resolvido", "Resolvido"),
        ("fechado", "Fechado"),
    ]

    # Aliases usados pelo template e view do Claude Design
    STATUS_CHOICES     = STATUS
    PRIORIDADE_CHOICES = PRIORIDADES

    assunto      = models.CharField(max_length=120, verbose_name="Assunto")
    descricao    = models.TextField(verbose_name="Descrição")
    origem       = models.CharField(max_length=30, choices=ORIGENS, verbose_name="Origem")
    categoria    = models.CharField(max_length=50, blank=True, verbose_name="Categoria")
    subcategoria = models.CharField(max_length=50, blank=True, verbose_name="Subcategoria")
    prioridade = models.CharField(max_length=10, choices=PRIORIDADES, default="media", verbose_name="Prioridade")
    status     = models.CharField(max_length=20, choices=STATUS, default="aberto", verbose_name="Status")
    aberto_em  = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    fechado_em = models.DateTimeField(null=True, blank=True)
    sla_horas  = models.PositiveIntegerField(default=8, verbose_name="SLA (horas)")
    departamento = models.ForeignKey(
        "Departamento", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="chamados", verbose_name="Departamento",
    )
    topico = models.ForeignKey(
        "Topico", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="chamados", verbose_name="Tópico",
    )
    ativo = models.ForeignKey(
        "Ativo", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="chamados", verbose_name="Ativo relacionado",
    )
    aberto_por = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="chamados_abertos", verbose_name="Aberto por",
    )
    agente = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="chamados_atribuidos", verbose_name="Agente",
    )

    class Meta:
        verbose_name = "Chamado"
        verbose_name_plural = "Chamados"
        ordering = ["-aberto_em"]

    def __str__(self):
        return f"#{self.pk} – {self.assunto} [{self.status}]"


class HistoricoChamado(models.Model):
    TIPO_CHOICES = [
        ("status",     "Alteração de Status"),
        ("prioridade", "Alteração de Prioridade"),
        ("atribuicao", "Atribuição"),
        ("comentario", "Comentário"),
    ]

    chamado = models.ForeignKey(
        Chamado, on_delete=models.CASCADE, related_name="historico",
    )
    autor = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Autor",
    )
    tipo           = models.CharField(max_length=20, choices=TIPO_CHOICES, blank=True)
    descricao      = models.CharField(max_length=200, blank=True)
    valor_anterior = models.CharField(max_length=100, blank=True, null=True)
    valor_novo     = models.CharField(max_length=100, blank=True, null=True)
    texto          = models.TextField(verbose_name="Texto", blank=True)
    quando         = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Histórico de Chamado"
        verbose_name_plural = "Históricos de Chamados"
        ordering = ["quando"]

    def __str__(self):
        return f"Chamado #{self.chamado_id} – {self.quando:%d/%m/%Y %H:%M}"


class AnexoChamado(models.Model):
    chamado     = models.ForeignKey(
        Chamado, on_delete=models.CASCADE, related_name="anexos",
    )
    enviado_por = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
    )
    arquivo   = models.FileField(
        upload_to="chamados/anexos/%Y/%m/",
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png", "txt"]),
            validar_tamanho_anexo,
        ],
    )
    quando    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"
        ordering = ["quando"]

    def __str__(self):
        return f"Anexo {self.pk} — Chamado #{self.chamado_id}"
