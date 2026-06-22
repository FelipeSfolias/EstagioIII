from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from apps.core.models import KanbanAuditLog, KanbanCard, KanbanColuna


class KanbanCardMoverTests(TestCase):
    def setUp(self):
        grp, _ = Group.objects.get_or_create(name="suporte")
        self.user = User.objects.create_user("sup", password="x")
        self.user.groups.add(grp)
        self.col_a = KanbanColuna.objects.create(
            chave="nao_iniciado", titulo="Não Iniciado", ordem=0
        )
        self.col_b = KanbanColuna.objects.create(
            chave="em_andamento", titulo="Em Andamento", ordem=1
        )
        self.card = KanbanCard.objects.create(titulo="Card Test", coluna=self.col_a)
        self.client = Client()
        self.client.login(username="sup", password="x")

    def _mover(self, coluna_key):
        return self.client.post(
            reverse("core:kanban_card_mover", kwargs={"pk": self.card.pk}),
            {"coluna_key": coluna_key},
        )

    def test_mover_cria_audit_log(self):
        self._mover("em_andamento")
        self.assertEqual(KanbanAuditLog.objects.filter(card=self.card).count(), 1)

    def test_log_registra_colunas_corretas(self):
        self._mover("em_andamento")
        log = KanbanAuditLog.objects.get(card=self.card)
        self.assertEqual(log.coluna_de, "nao_iniciado")
        self.assertEqual(log.coluna_para, "em_andamento")

    def test_log_registra_usuario(self):
        self._mover("em_andamento")
        log = KanbanAuditLog.objects.get(card=self.card)
        self.assertEqual(log.usuario, self.user)

    def test_mover_para_mesma_coluna_noop_sem_log(self):
        self._mover("nao_iniciado")
        self.assertEqual(KanbanAuditLog.objects.filter(card=self.card).count(), 0)

    def test_coluna_inexistente_retorna_404(self):
        resp = self._mover("nao_existe")
        self.assertEqual(resp.status_code, 404)

    def test_coluna_key_vazia_retorna_400(self):
        resp = self.client.post(
            reverse("core:kanban_card_mover", kwargs={"pk": self.card.pk}),
            {"coluna_key": ""},
        )
        self.assertEqual(resp.status_code, 400)

    def test_movimentar_duas_vezes_cria_dois_logs(self):
        self._mover("em_andamento")
        self._mover("nao_iniciado")
        self.assertEqual(KanbanAuditLog.objects.filter(card=self.card).count(), 2)
