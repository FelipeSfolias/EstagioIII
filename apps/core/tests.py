from django.test import TestCase
from django.core.exceptions import ValidationError

from .models import Local


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
