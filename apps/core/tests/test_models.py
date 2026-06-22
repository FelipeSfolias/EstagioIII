from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.models import Ativo, ItemEstoque, KanbanCard, KanbanColuna, Local


class LocalHierarquiaTests(TestCase):
    def test_pai_de_si_mesmo_falha(self):
        a = Local.objects.create(codigo="A", nome="A", tipo="Site")
        a.pai = a
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_ciclo_indireto_falha(self):
        a = Local.objects.create(codigo="A", nome="A", tipo="Site")
        b = Local.objects.create(codigo="B", nome="B", tipo="Prédio", pai=a)
        c = Local.objects.create(codigo="C", nome="C", tipo="Sala", pai=b)
        a.pai = c
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_hierarquia_valida_passa(self):
        a = Local.objects.create(codigo="A", nome="A", tipo="Site")
        b = Local.objects.create(codigo="B", nome="B", tipo="Prédio", pai=a)
        b.full_clean()  # não deve lançar


class AtivoProximoPatrimonioTests(TestCase):
    def test_primeiro_ativo_gera_0001(self):
        self.assertEqual(Ativo.proximo_patrimonio("Notebook"), "Note-0001")

    def test_sequencia_incrementa(self):
        Ativo.objects.create(patrimonio="Note-0001", modelo="X", categoria="Notebook")
        self.assertEqual(Ativo.proximo_patrimonio("Notebook"), "Note-0002")

    def test_suporta_numeros_acima_9999(self):
        Ativo.objects.create(patrimonio="Note-9999", modelo="X", categoria="Notebook")
        Ativo.objects.create(patrimonio="Note-10000", modelo="Y", categoria="Notebook")
        self.assertEqual(Ativo.proximo_patrimonio("Notebook"), "Note-10001")

    def test_categoria_diferente_nao_interfere(self):
        Ativo.objects.create(patrimonio="Desk-0005", modelo="X", categoria="Desktop")
        self.assertEqual(Ativo.proximo_patrimonio("Notebook"), "Note-0001")

    def test_categoria_desconhecida_usa_outr(self):
        result = Ativo.proximo_patrimonio("Inexistente")
        self.assertTrue(result.startswith("Outr-"))


class ItemEstoqueAbaixoMinimoTests(TestCase):
    def test_abaixo_minimo_true(self):
        item = ItemEstoque(sku="X", nome="X", nivel_minimo=10, qtde=5)
        self.assertTrue(item.abaixo_minimo)

    def test_igual_minimo_false(self):
        item = ItemEstoque(sku="X", nome="X", nivel_minimo=5, qtde=5)
        self.assertFalse(item.abaixo_minimo)

    def test_acima_minimo_false(self):
        item = ItemEstoque(sku="X", nome="X", nivel_minimo=5, qtde=10)
        self.assertFalse(item.abaixo_minimo)

    def test_nivel_zero_nunca_abaixo(self):
        item = ItemEstoque(sku="X", nome="X", nivel_minimo=0, qtde=0)
        self.assertFalse(item.abaixo_minimo)


class KanbanCardAtrasadoTests(TestCase):
    def setUp(self):
        self.col_anda = KanbanColuna.objects.create(
            chave="em_andamento", titulo="Em Andamento", ordem=0
        )
        self.col_conc = KanbanColuna.objects.create(
            chave="concluido", titulo="Concluído", ordem=1
        )

    def test_prazo_vencido_atrasado(self):
        ontem = date.today() - timedelta(days=1)
        card = KanbanCard(titulo="X", coluna=self.col_anda, prazo=ontem)
        self.assertTrue(card.atrasado)

    def test_sem_prazo_nao_atrasado(self):
        card = KanbanCard(titulo="X", coluna=self.col_anda, prazo=None)
        self.assertFalse(card.atrasado)

    def test_concluido_nao_atrasado_mesmo_com_prazo_vencido(self):
        ontem = date.today() - timedelta(days=1)
        card = KanbanCard(titulo="X", coluna=self.col_conc, prazo=ontem)
        self.assertFalse(card.atrasado)

    def test_prazo_futuro_nao_atrasado(self):
        amanha = date.today() + timedelta(days=1)
        card = KanbanCard(titulo="X", coluna=self.col_anda, prazo=amanha)
        self.assertFalse(card.atrasado)
