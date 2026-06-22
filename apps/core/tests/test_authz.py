from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from apps.core.authz import tier_required


class TierRequiredTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin_grp = Group.objects.create(name="admin")
        self.suporte_grp = Group.objects.create(name="suporte")

    def _wrap(self, user):
        @tier_required("admin")
        def view(request):
            return HttpResponse("ok")

        req = self.factory.get("/")
        req.user = user
        return view(req)

    def test_anonimo_redireciona(self):
        resp = self._wrap(AnonymousUser())
        self.assertEqual(resp.status_code, 302)

    def test_superuser_passa(self):
        u = User.objects.create_superuser("su", "su@x.com", "x")
        resp = self._wrap(u)
        self.assertEqual(resp.status_code, 200)

    def test_grupo_correto_passa(self):
        u = User.objects.create_user("a", password="x")
        u.groups.add(self.admin_grp)
        resp = self._wrap(u)
        self.assertEqual(resp.status_code, 200)

    def test_grupo_errado_nega(self):
        u = User.objects.create_user("s", password="x")
        u.groups.add(self.suporte_grp)
        with self.assertRaises(PermissionDenied):
            self._wrap(u)

    def test_multiplos_tiers_aceita_qualquer(self):
        """Usuário com qualquer dos tiers listados deve ter acesso."""
        @tier_required("suporte", "admin")
        def view(request):
            return HttpResponse("ok")

        u = User.objects.create_user("sup", password="x")
        u.groups.add(self.suporte_grp)
        req = self.factory.get("/")
        req.user = u
        resp = view(req)
        self.assertEqual(resp.status_code, 200)
