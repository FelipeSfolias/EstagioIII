from django.db import migrations

SEED = {
    "Compras": [
        "Solicitação de Compra",
        "Cotação",
        "Reembolso",
    ],
    "Manutenção": [
        "Predial",
        "Elétrica",
        "Hidráulica",
        "Mobiliário",
    ],
    "Suporte": [
        "Assistência Técnica Equipamentos",
        "Acesso / Senha",
        "E-mail",
        "Software / ERP",
        "Rede / Internet",
    ],
}


def seed_forward(apps, schema_editor):
    Departamento = apps.get_model("core", "Departamento")
    Topico = apps.get_model("core", "Topico")
    for dept_nome, topicos in SEED.items():
        dept = Departamento.objects.create(nome=dept_nome, ativo=True)
        for t in topicos:
            Topico.objects.create(departamento=dept, nome=t, ativo=True)


def seed_backward(apps, schema_editor):
    Departamento = apps.get_model("core", "Departamento")
    Departamento.objects.filter(nome__in=SEED.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_departamento_topico_chamado_fk"),
    ]

    operations = [
        migrations.RunPython(seed_forward, seed_backward),
    ]
