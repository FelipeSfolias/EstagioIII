from django.core.exceptions import ValidationError
from django.db import models


class Local(models.Model):
    TIPOS = [
        ("Site", "Site"),
        ("Prédio", "Prédio"),
        ("Andar", "Andar"),
        ("Sala", "Sala"),
        ("Rack", "Rack"),
    ]

    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=30, choices=TIPOS)
    pai = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="filhos",
    )

    class Meta:
        verbose_name = "Local"
        verbose_name_plural = "Locais"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} – {self.nome}"

    def clean(self):
        super().clean()
        if self.pai_id is not None and self.pai_id == self.pk:
            raise ValidationError({"pai": "Um local não pode ser pai de si mesmo."})

        visitados = set()
        atual = self.pai
        while atual is not None:
            if atual.pk in visitados or atual.pk == self.pk:
                raise ValidationError({"pai": "Hierarquia inválida: ciclo detectado."})
            visitados.add(atual.pk)
            atual = atual.pai

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def caminho(self):
        parts = []
        atual = self
        while atual is not None:
            parts.append(atual.nome)
            atual = atual.pai
        return ' › '.join(reversed(parts))
