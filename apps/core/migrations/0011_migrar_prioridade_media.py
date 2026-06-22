from django.db import migrations


def migrar_prioridade(apps, schema_editor):
    Chamado = apps.get_model("core", "Chamado")
    Chamado.objects.filter(prioridade="média").update(prioridade="media")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_alterar_prioridade_e_rename_patrimonio"),
    ]

    operations = [
        migrations.RunPython(migrar_prioridade, migrations.RunPython.noop),
    ]
