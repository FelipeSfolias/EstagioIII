from django.db import migrations


def seed_locais_itens(apps, schema_editor):
    Local = apps.get_model("core", "Local")
    ItemEstoque = apps.get_model("core", "ItemEstoque")

    if Local.objects.exists() or ItemEstoque.objects.exists():
        return

    matriz = Local.objects.create(codigo="MATRIZ", nome="Matriz", tipo="Site", pai=None)
    bloco = Local.objects.create(codigo="BL01", nome="Bloco 01", tipo="Prédio", pai=matriz)
    Local.objects.create(codigo="TI-01", nome="Sala TI", tipo="Sala", pai=bloco)

    ItemEstoque.objects.create(sku="CAB-RJ45",   nome="Cabo de Rede RJ45 2m", unidade="pc", nivel_minimo=10, qtde=25)
    ItemEstoque.objects.create(sku="MOUSE-USB",  nome="Mouse USB",             unidade="pc", nivel_minimo=5,  qtde=3)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_kanbancard"),
    ]

    operations = [
        migrations.RunPython(seed_locais_itens, migrations.RunPython.noop),
    ]
