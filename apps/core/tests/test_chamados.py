from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from apps.core.models import Chamado, HistoricoChamado


def _make_user(username, group_name, password="testpass"):
    grp, _ = Group.objects.get_or_create(name=group_name)
    u = User.objects.create_user(username, password=password)
    u.groups.add(grp)
    return u


class AbrirChamadoTests(TestCase):
    def setUp(self):
        self.colab = _make_user("colab", "colaborador")
        self.client = Client()
        self.client.login(username="colab", password="testpass")

    def test_colaborador_abre_com_prioridade_baixa(self):
        self.client.post(reverse("core:chamado_novo"), {
            "assunto": "Wi-Fi caiu", "descricao": "Desc",
            "origem": "Infra", "prioridade": "alta",
        })
        c = Chamado.objects.get(assunto="Wi-Fi caiu")
        self.assertEqual(c.status, "aberto")
        self.assertEqual(c.prioridade, "baixa")

    def test_aberto_por_preenchido(self):
        self.client.post(reverse("core:chamado_novo"), {
            "assunto": "Teste aberto_por", "descricao": "D",
            "origem": "Infra", "prioridade": "media",
        })
        c = Chamado.objects.get(assunto="Teste aberto_por")
        self.assertEqual(c.aberto_por, self.colab)

    def test_redirect_apos_criar(self):
        resp = self.client.post(reverse("core:chamado_novo"), {
            "assunto": "Redirect test", "descricao": "D",
            "origem": "Suporte", "prioridade": "media",
        })
        self.assertRedirects(resp, reverse("core:meus_chamados"))


class AtualizarChamadoTests(TestCase):
    def setUp(self):
        self.colab = _make_user("col", "colaborador")
        self.suporte = _make_user("sup", "suporte")
        self.chamado = Chamado.objects.create(
            assunto="Chamado Teste", descricao="Desc",
            origem="Infra", prioridade="media", aberto_por=self.colab,
        )
        self.client = Client()
        self.client.login(username="sup", password="testpass")
        self.url = reverse("core:chamado_atualizar", kwargs={"cid": self.chamado.pk})

    def test_resolver_preenche_fechado_em(self):
        self.client.post(self.url, {"novo_status": "resolvido", "prioridade": "media"})
        self.chamado.refresh_from_db()
        self.assertEqual(self.chamado.status, "resolvido")
        self.assertIsNotNone(self.chamado.fechado_em)

    def test_reabrir_limpa_fechado_em(self):
        self.chamado.status = "resolvido"
        from django.utils import timezone
        self.chamado.fechado_em = timezone.now()
        self.chamado.save()
        self.client.post(self.url, {"novo_status": "aberto", "prioridade": "media"})
        self.chamado.refresh_from_db()
        self.assertIsNone(self.chamado.fechado_em)

    def test_historico_mudanca_status(self):
        self.client.post(self.url, {"novo_status": "em_atendimento", "prioridade": "media"})
        self.assertTrue(
            HistoricoChamado.objects.filter(
                chamado=self.chamado, tipo="status", valor_novo="em_atendimento"
            ).exists()
        )

    def test_historico_mudanca_prioridade(self):
        self.client.post(self.url, {"novo_status": "aberto", "prioridade": "alta"})
        self.assertTrue(
            HistoricoChamado.objects.filter(chamado=self.chamado, tipo="prioridade").exists()
        )

    def test_comentario_sem_mudancas_cria_historico_comentario(self):
        self.client.post(self.url, {
            "novo_status": "aberto", "prioridade": "media",
            "comentario": "Verificando o problema",
        })
        self.assertTrue(
            HistoricoChamado.objects.filter(chamado=self.chamado, tipo="comentario").exists()
        )

    def test_status_invalido_rejeitado(self):
        self.client.post(self.url, {"novo_status": "hackeado", "prioridade": "media"})
        self.chamado.refresh_from_db()
        self.assertNotEqual(self.chamado.status, "hackeado")
        self.assertEqual(self.chamado.status, "aberto")

    def test_colaborador_nao_pode_atualizar(self):
        client2 = Client()
        client2.login(username="col", password="testpass")
        resp = client2.post(self.url, {"novo_status": "resolvido", "prioridade": "media"})
        # tier_required("suporte", "admin") levanta PermissionDenied → 403
        self.assertEqual(resp.status_code, 403)
