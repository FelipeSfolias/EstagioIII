from django.db import models


class Departamento(models.Model):
    nome  = models.CharField(max_length=100, verbose_name="Nome")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Topico(models.Model):
    departamento = models.ForeignKey(
        Departamento, on_delete=models.CASCADE,
        related_name="topicos", verbose_name="Departamento",
    )
    nome  = models.CharField(max_length=100, verbose_name="Nome")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Tópico"
        verbose_name_plural = "Tópicos"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.departamento.nome} › {self.nome}"
