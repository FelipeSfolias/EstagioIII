from django.test import TestCase

from apps.core.forms import AtivoForm


class AtivoFormTests(TestCase):
    def _form(self, patrimonio, categoria):
        return AtivoForm(data={
            "patrimonio": patrimonio,
            "numero_serie": "",
            "modelo": "Test Model",
            "categoria": categoria,
            "estado": "estoque",
            "local": "",
        })

    def test_formato_invalido_rejeitado(self):
        form = self._form("ABC-123", "Notebook")
        self.assertFalse(form.is_valid())
        self.assertIn("patrimonio", form.errors)

    def test_prefixo_incompativel_rejeitado(self):
        form = self._form("Note-0001", "Desktop")
        self.assertFalse(form.is_valid())
        self.assertIn("patrimonio", form.errors)

    def test_combinacao_valida_aceita(self):
        form = self._form("Note-0001", "Notebook")
        self.assertTrue(form.is_valid(), form.errors)

    def test_formato_sem_hifem_rejeitado(self):
        form = self._form("Note0001", "Notebook")
        self.assertFalse(form.is_valid())
        self.assertIn("patrimonio", form.errors)

    def test_prefixo_case_insensitive(self):
        form = self._form("note-0001", "Notebook")
        self.assertTrue(form.is_valid(), form.errors)
