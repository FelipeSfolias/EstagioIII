from django.db import models


class Ativo(models.Model):
    CATEGORIAS = [
        ("Notebook", "Notebook"),
        ("Desktop", "Desktop"),
        ("Monitor", "Monitor"),
        ("Nobreak", "Nobreak"),
        ("Smartphone", "Smartphone"),
        ("Servidor", "Servidor"),
        ("Impressora", "Impressora"),
        ("Switch", "Switch"),
        ("Outro", "Outro"),
    ]

    PREFIXOS = {
        "Notebook":   "Note",
        "Desktop":    "Desk",
        "Monitor":    "Moni",
        "Nobreak":    "Nobr",
        "Smartphone": "Smar",
        "Servidor":   "Serv",
        "Impressora": "Impr",
        "Switch":     "Swit",
        "Outro":      "Outr",
    }

    @classmethod
    def proximo_patrimonio(cls, categoria: str) -> str:
        prefixo = cls.PREFIXOS.get(categoria, "Outr")
        max_num = 0
        for pat in cls.objects.filter(
            patrimonio__istartswith=f"{prefixo}-"
        ).values_list("patrimonio", flat=True):
            try:
                num = int(pat.split("-", 1)[1])
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue
        return f"{prefixo}-{max_num + 1:04d}"
    ESTADOS = [
        ("em_uso", "Em Uso"),
        ("estoque", "Estoque"),
        ("manutencao", "Manutenção"),
        ("descartado", "Descartado"),
    ]

    patrimonio = models.CharField(max_length=20, unique=True, verbose_name="Patrimônio")
    numero_serie = models.CharField(max_length=100, blank=True, verbose_name="Número de Série")
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    categoria = models.CharField(max_length=30, choices=CATEGORIAS, verbose_name="Categoria")
    estado = models.CharField(max_length=20, choices=ESTADOS, default="estoque", verbose_name="Estado")
    local = models.ForeignKey(
        "Local",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ativos",
        verbose_name="Local",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ativo"
        verbose_name_plural = "Ativos"
        ordering = ["patrimonio"]

    def __str__(self):
        return f"{self.patrimonio} – {self.modelo}"
