from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_criar_grupos_acesso"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Quadro",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=200)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("criado_por", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="quadros_criados", to=settings.AUTH_USER_MODEL)),
                ("membros", models.ManyToManyField(blank=True, related_name="quadros_membro", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["nome"]},
        ),
        migrations.CreateModel(
            name="Lista",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=100)),
                ("cor", models.CharField(default="#6b7280", max_length=20)),
                ("posicao", models.PositiveIntegerField(default=0)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("quadro", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="listas", to="core.quadro")),
            ],
            options={"ordering": ["posicao", "id"]},
        ),
        migrations.CreateModel(
            name="Etiqueta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nome", models.CharField(max_length=80)),
                ("cor", models.CharField(default="#2563eb", max_length=20)),
                ("quadro", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="etiquetas", to="core.quadro")),
            ],
        ),
        migrations.CreateModel(
            name="Cartao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("titulo", models.CharField(max_length=300)),
                ("descricao", models.TextField(blank=True)),
                ("progresso", models.PositiveSmallIntegerField(default=0)),
                ("posicao", models.PositiveIntegerField(default=0)),
                ("area", models.CharField(blank=True, max_length=100)),
                ("capa_cor", models.CharField(blank=True, max_length=20)),
                ("concluido", models.BooleanField(default=False)),
                ("data_inicio", models.DateField(blank=True, null=True)),
                ("data_entrega", models.DateTimeField(blank=True, null=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("lista", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cartoes", to="core.lista")),
                ("etiquetas", models.ManyToManyField(blank=True, related_name="cartoes", to="core.etiqueta")),
                ("membros", models.ManyToManyField(blank=True, related_name="cartoes_kanban", to=settings.AUTH_USER_MODEL)),
                ("criado_por", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="cartoes_criados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["posicao", "id"]},
        ),
        migrations.CreateModel(
            name="ChecklistKanban",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("titulo", models.CharField(default="Checklist", max_length=200)),
                ("posicao", models.PositiveIntegerField(default=0)),
                ("cartao", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="checklists", to="core.cartao")),
            ],
            options={"ordering": ["posicao", "id"]},
        ),
        migrations.CreateModel(
            name="ItemChecklistKanban",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("texto", models.CharField(max_length=500)),
                ("concluido", models.BooleanField(default=False)),
                ("posicao", models.PositiveIntegerField(default=0)),
                ("checklist", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="itens", to="core.checklistkanban")),
            ],
            options={"ordering": ["posicao", "id"]},
        ),
        migrations.CreateModel(
            name="AtividadeCartao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("tipo", models.CharField(choices=[("atividade", "Atividade"), ("comentario", "Comentário")], default="atividade", max_length=20)),
                ("texto", models.TextField()),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("cartao", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="atividades", to="core.cartao")),
                ("autor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="atividades_kanban", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-criado_em"]},
        ),
    ]
