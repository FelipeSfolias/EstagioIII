from django.db import models


class ItemEstoque(models.Model):
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU")
    nome = models.CharField(max_length=150, verbose_name="Nome")
    unidade = models.CharField(max_length=20, default="pc", verbose_name="Unidade")
    nivel_minimo = models.PositiveIntegerField(default=0, verbose_name="Nível mínimo")
    qtde = models.PositiveIntegerField(default=0, verbose_name="Quantidade")

    class Meta:
        verbose_name = "Item de Estoque"
        verbose_name_plural = "Itens de Estoque"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.sku} – {self.nome}"

    @property
    def abaixo_minimo(self):
        return self.qtde < self.nivel_minimo

    @property
    def status_estoque(self):
        if self.qtde == 0:
            return "esgotado"
        if self.qtde < self.nivel_minimo:
            return "abaixo_minimo"
        return "ok"
