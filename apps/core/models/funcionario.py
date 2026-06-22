from django.db import models
from django.contrib.auth.models import User


UF_CHOICES = [
    ("AC", "Acre"), ("AL", "Alagoas"), ("AP", "Amapá"), ("AM", "Amazonas"),
    ("BA", "Bahia"), ("CE", "Ceará"), ("DF", "Distrito Federal"), ("ES", "Espírito Santo"),
    ("GO", "Goiás"), ("MA", "Maranhão"), ("MT", "Mato Grosso"), ("MS", "Mato Grosso do Sul"),
    ("MG", "Minas Gerais"), ("PA", "Pará"), ("PB", "Paraíba"), ("PR", "Paraná"),
    ("PE", "Pernambuco"), ("PI", "Piauí"), ("RJ", "Rio de Janeiro"), ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"), ("RO", "Rondônia"), ("RR", "Roraima"), ("SC", "Santa Catarina"),
    ("SP", "São Paulo"), ("SE", "Sergipe"), ("TO", "Tocantins"),
]


class Funcionario(models.Model):
    nome = models.CharField(max_length=150, verbose_name="Nome")
    email = models.EmailField(unique=True, verbose_name="E-mail")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF",
                           help_text="Formato: 000.000.000-00")
    contato = models.CharField(max_length=20, blank=True, verbose_name="Contato")
    ramal = models.CharField(max_length=10, blank=True, verbose_name="Ramal")
    funcao = models.CharField(max_length=100, verbose_name="Função")
    setor = models.CharField(max_length=100, verbose_name="Setor")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    uf = models.CharField(max_length=2, choices=UF_CHOICES, verbose_name="UF")
    ativo_atribuido = models.ForeignKey(
        "Ativo",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="custodiantes",
        verbose_name="Patrimônio atribuído",
    )
    usuario = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="funcionario",
        verbose_name="Usuário do sistema",
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} – {self.funcao}"
