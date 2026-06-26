import re

from django import forms
from django.contrib.auth.models import Group, User
from .models import Funcionario, Ativo, Local, ItemEstoque, Chamado

_PERFIL_CHOICES = [
    ("", "— Nenhum —"),
    ("colaborador", "Colaborador"),
    ("suporte", "Suporte"),
    ("admin", "Admin"),
]


class FuncionarioForm(forms.ModelForm):
    perfil = forms.ChoiceField(
        choices=_PERFIL_CHOICES,
        required=False,
        label="Perfil de acesso",
        widget=forms.Select(attrs={"class": "input-lite"}),
    )
    username = forms.CharField(
        required=False,
        label="Login (usuário do sistema)",
        widget=forms.TextInput(attrs={"placeholder": "Ex: joao.silva", "class": "input-lite"}),
    )
    nova_senha = forms.CharField(
        required=False,
        label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Nova senha", "class": "input-lite"}),
    )
    confirmar_senha = forms.CharField(
        required=False,
        label="Confirmar senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Repita a senha", "class": "input-lite"}),
    )

    class Meta:
        model = Funcionario
        fields = [
            "nome", "email", "cpf", "contato", "ramal",
            "funcao", "setor", "cidade", "uf",
            "ativo_atribuido", "ativo",
        ]
        widgets = {
            "nome":     forms.TextInput(attrs={"placeholder": "Nome completo"}),
            "email":    forms.EmailInput(attrs={"placeholder": "nome@empresa.com"}),
            "cpf":      forms.TextInput(attrs={"placeholder": "000.000.000-00", "maxlength": "14"}),
            "contato":  forms.TextInput(attrs={"placeholder": "(00) 90000-0000"}),
            "ramal":    forms.TextInput(attrs={"placeholder": "Ex: 1042"}),
            "funcao":   forms.TextInput(attrs={"placeholder": "Ex: Analista de TI"}),
            "setor":    forms.TextInput(attrs={"placeholder": "Ex: Infraestrutura"}),
            "cidade":   forms.TextInput(attrs={"placeholder": "Ex: Porto Alegre"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        ativos_ocupados = (
            Funcionario.objects
            .filter(ativo_atribuido__isnull=False)
            .exclude(pk=instance.pk if instance else None)
            .values_list("ativo_atribuido_id", flat=True)
        )
        self.fields["ativo_atribuido"].queryset = Ativo.objects.exclude(pk__in=ativos_ocupados)
        self.fields["ativo_atribuido"].empty_label = "— Nenhum —"
        if instance and instance.usuario_id:
            self.initial["username"] = instance.usuario.username
            for nome_grupo in ("admin", "suporte", "colaborador"):
                if instance.usuario.groups.filter(name=nome_grupo).exists():
                    self.initial["perfil"] = nome_grupo
                    break
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.Select)):
                field.widget.attrs.setdefault("class", "input-lite")

    def clean(self):
        cleaned = super().clean()
        username = (cleaned.get("username") or "").strip()
        senha = cleaned.get("nova_senha") or ""
        confirmar = cleaned.get("confirmar_senha") or ""

        if senha and senha != confirmar:
            self.add_error("confirmar_senha", "As senhas não conferem.")

        # Novo usuário: username obrigatório e senha obrigatória
        instance = self.instance if self.instance and self.instance.pk else None
        tem_usuario = instance and instance.usuario_id
        if not tem_usuario and username:
            if User.objects.filter(username=username).exists():
                self.add_error("username", "Este nome de usuário já está em uso.")
            if not senha:
                self.add_error("nova_senha", "Informe a senha para criar o acesso ao sistema.")

        return cleaned

    def save(self, commit=True):
        func = super().save(commit=commit)
        if not commit:
            return func

        username = (self.cleaned_data.get("username") or "").strip()
        senha = self.cleaned_data.get("nova_senha") or ""

        # Cria um novo User se ainda não tem um vinculado
        if not func.usuario_id and username:
            user = User.objects.create_user(
                username=username,
                email=func.email,
                password=senha or None,
            )
            func.usuario = user
            func.save(update_fields=["usuario"])
        elif func.usuario_id and senha:
            func.usuario.set_password(senha)
            func.usuario.save(update_fields=["password"])

        # Atribui o grupo de perfil
        if func.usuario_id:
            perfil = self.cleaned_data.get("perfil") or ""
            func.usuario.groups.clear()
            if perfil:
                grupo, _ = Group.objects.get_or_create(name=perfil)
                func.usuario.groups.add(grupo)

        return func


# ── Cadastro de Locais ──────────────────────────────────────────────
class LocalForm(forms.ModelForm):
    class Meta:
        model = Local
        fields = ["codigo", "nome", "tipo", "pai"]
        widgets = {
            "codigo": forms.TextInput(attrs={"placeholder": "Ex: TI-01"}),
            "nome":   forms.TextInput(attrs={"placeholder": "Ex: Sala TI"}),
            "pai":    forms.Select(attrs={"class": "input-lite"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pai"].empty_label = "— Raiz —"
        if self.instance and self.instance.pk:
            descendentes = self._coletar_descendentes(self.instance)
            self.fields["pai"].queryset = Local.objects.exclude(
                pk__in=descendentes | {self.instance.pk}
            )
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "input-lite")

    @staticmethod
    def _coletar_descendentes(local):
        resultado = set()
        fila = list(local.filhos.all())
        while fila:
            atual = fila.pop()
            if atual.pk not in resultado:
                resultado.add(atual.pk)
                fila.extend(atual.filhos.all())
        return resultado


# ── Cadastro de Ativos ──────────────────────────────────────────────
class AtivoForm(forms.ModelForm):
    class Meta:
        model = Ativo
        fields = ["patrimonio", "numero_serie", "modelo", "categoria", "estado", "local"]
        widgets = {
            "patrimonio":   forms.TextInput(attrs={"placeholder": "Ex: NOTE-0001"}),
            "numero_serie": forms.TextInput(attrs={"placeholder": "Opcional"}),
            "modelo":       forms.TextInput(attrs={"placeholder": "Ex: Dell Latitude 5520"}),
            "local":        forms.Select(attrs={"class": "input-lite"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["local"].empty_label = "— Nenhum —"
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "input-lite")

    def clean(self):
        cleaned = super().clean()
        patrimonio = (cleaned.get("patrimonio") or "").strip()
        categoria = cleaned.get("categoria") or ""

        if not re.fullmatch(r"[A-Za-z]{4}-\d{4}", patrimonio):
            self.add_error(
                "patrimonio",
                "Formato inválido. Use 4 letras + hífen + 4 dígitos (ex: Note-0001).",
            )
            return cleaned

        prefixo_esperado = Ativo.PREFIXOS.get(categoria, "")
        prefixo_informado = patrimonio[:4]
        if prefixo_esperado and prefixo_informado.lower() != prefixo_esperado.lower():
            self.add_error(
                "patrimonio",
                f"Para a categoria '{categoria}' o prefixo deve ser '{prefixo_esperado}' "
                f"(ex: {prefixo_esperado}-0001).",
            )
        return cleaned


# ── Cadastro de Itens de Estoque ────────────────────────────────────
class ItemEstoqueForm(forms.ModelForm):
    class Meta:
        model = ItemEstoque
        fields = ["nome", "unidade", "nivel_minimo", "qtde"]
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Ex: Cabo de Rede RJ45 2m"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "input-lite")


# ── Abrir Chamado ───────────────────────────────────────────────────
class AbrirChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ["assunto", "descricao", "origem", "prioridade", "ativo"]
        widgets = {
            "assunto":   forms.TextInput(attrs={"placeholder": "Assunto do chamado"}),
            "descricao": forms.Textarea(attrs={"rows": 5, "placeholder": "Descreva o problema ou solicitação..."}),
            "ativo":     forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ativo"].empty_label = "— Nenhum —"
        self.fields["ativo"].required = False
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "input-lite")


# ── Responder / Atualizar Chamado ────────────────────────────────────
class ResponderChamadoForm(forms.Form):
    novo_status = forms.ChoiceField(
        choices=Chamado.STATUS,
        label="Status",
        widget=forms.Select(attrs={"class": "ch-form-select"}),
    )
    prioridade = forms.ChoiceField(
        choices=Chamado.PRIORIDADES,
        label="Prioridade",
        widget=forms.Select(attrs={"class": "ch-form-select"}),
    )
    agente = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Agente",
        empty_label="— Não atribuído —",
        widget=forms.Select(attrs={"class": "ch-form-select"}),
    )
    comentario = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Comentário ou observação...",
            "class": "ch-form-textarea",
        }),
        required=False,
        label="Comentário",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["agente"].queryset = (
            User.objects.filter(groups__name__in=["admin", "suporte"])
            .distinct()
            .order_by("username")
        )
