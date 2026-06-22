from django.db import migrations


def criar_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for nome in ("colaborador", "suporte", "admin"):
        Group.objects.get_or_create(name=nome)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_migrar_prioridade_media"),
    ]

    operations = [
        migrations.RunPython(criar_grupos, migrations.RunPython.noop),
    ]
