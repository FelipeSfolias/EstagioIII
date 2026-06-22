from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # Cadastros
    path("cadastros/usuarios/", views.cad_usuarios, name="cad_usuarios"),
    path("cadastros/usuarios/<int:uid>/editar/", views.usuario_editar, name="usuario_editar"),
    path("cadastros/usuarios/<int:uid>/excluir/", views.usuario_excluir, name="usuario_excluir"),
    path("cadastros/locais/", views.cad_locais, name="cad_locais"),
    path("cadastros/locais/<int:lid>/editar/", views.local_editar, name="local_editar"),
    path("cadastros/locais/<int:lid>/excluir/", views.local_excluir, name="local_excluir"),
    path("cadastros/ativos/", views.cad_ativos, name="cad_ativos"),
    path("cadastros/ativos/buscar/", views.ativo_buscar, name="ativo_buscar"),
    path("cadastros/funcionarios/buscar/", views.funcionario_buscar, name="funcionario_buscar"),
    path("cadastros/ativos/proximo-patrimonio/", views.ativo_proximo_patrimonio, name="ativo_proximo_patrimonio"),
    path("cadastros/ativos/<int:aid>/editar/", views.ativo_editar, name="ativo_editar"),
    path("cadastros/ativos/<int:aid>/excluir/", views.ativo_excluir, name="ativo_excluir"),
    path("cadastros/itens-estoque/", views.cad_itens_estoque, name="cad_itens_estoque"),
    path("cadastros/itens/<int:iid>/editar/", views.item_editar, name="item_editar"),
    path("cadastros/itens/<int:iid>/excluir/", views.item_excluir, name="item_excluir"),
    path("cadastros/itens/<int:iid>/ajustar/", views.item_ajustar_qtde, name="item_ajustar_qtde"),
    # Patrimônios
    path("patrimonios/", views.patrimonios_lista, name="patrimonios_lista"),
    # Chamados
    path("chamados/novo/", views.chamado_novo, name="chamado_novo"),
    path("chamados/indicadores/", views.chamados_indicadores, name="chamados_indicadores"),
    path("chamados/abrir-tier/", views.chamado_criar_tier, name="chamado_criar_tier"),
    path("chamados/buscar-colaborador/", views.colaborador_buscar, name="colaborador_buscar"),
    path("chamados/ativos-meus/", views.ativos_meus, name="ativos_meus"),
    path("chamados/todos/", views.chamados_todos, name="chamados_todos"),
    path("chamados/todos/meus/", views.chamados_todos_meus, name="chamados_todos_meus"),
    path("chamados/todos/fechados/", views.chamados_todos_fechados, name="chamados_todos_fechados"),
    path("chamados/todos/acao-massa/", views.chamado_acao_massa, name="chamado_acao_massa"),
    path("chamados/meus/", views.meus_chamados, name="meus_chamados"),
    path("chamados/<int:cid>/", views.chamado_detalhe, name="chamado_detalhe"),
    path("chamados/<int:cid>/atualizar/", views.chamado_atualizar, name="chamado_atualizar"),
    path("chamados/<int:cid>/atribuir/", views.chamado_atribuir, name="chamado_atribuir"),
    path("chamados/<int:cid>/fechar/", views.chamado_fechar, name="chamado_fechar"),
    path("chamados/<int:cid>/anexar/", views.chamado_anexar, name="chamado_anexar"),
    # Projetos / Kanban rico
    path("projetos/kanban/", views.projetos_kanban, name="projetos_kanban"),
    path("projetos/kanban/<int:quadro_id>/", views.projetos_kanban, name="projetos_kanban_quadro"),
    path("projetos/kanban/criar/", views.kanban_quadro_criar, name="kanban_quadro_criar"),
    path("projetos/indicadores/", views.projetos_indicadores, name="projetos_indicadores"),
    path("projetos/card/<int:pk>/", views.card_editar, name="card_editar"),
    # Listas
    path("projetos/kanban/<int:quadro_id>/lista/nova/", views.kanban_lista_criar, name="kanban_lista_criar"),
    # Cartões (novo kanban)
    path("projetos/kanban/cartao/novo/", views.kanban_cartao_criar, name="kanban_cartao_criar"),
    path("projetos/kanban/cartao/<int:pk>/", views.kanban_cartao_detail, name="kanban_cartao_detail"),
    path("projetos/kanban/cartao/<int:pk>/atualizar/", views.kanban_cartao_atualizar, name="kanban_cartao_atualizar"),
    path("projetos/kanban/cartao/<int:pk>/mover/", views.kanban_cartao_mover, name="kanban_cartao_mover"),
    path("projetos/kanban/cartao/<int:pk>/excluir/", views.kanban_cartao_excluir, name="kanban_cartao_excluir"),
    path("projetos/kanban/cartao/<int:pk>/etiqueta/", views.kanban_cartao_etiqueta, name="kanban_cartao_etiqueta"),
    path("projetos/kanban/cartao/<int:pk>/membro/", views.kanban_cartao_membro, name="kanban_cartao_membro"),
    path("projetos/kanban/cartao/<int:pk>/comentar/", views.kanban_cartao_comentar, name="kanban_cartao_comentar"),
    path("projetos/kanban/cartao/<int:pk>/checklist/", views.kanban_checklist_criar, name="kanban_checklist_criar"),
    path("projetos/kanban/checklist/<int:pk>/excluir/", views.kanban_checklist_excluir, name="kanban_checklist_excluir"),
    path("projetos/kanban/checklist/<int:pk>/item/novo/", views.kanban_checklist_item_criar, name="kanban_checklist_item_criar"),
    path("projetos/kanban/item/<int:pk>/toggle/", views.kanban_item_toggle, name="kanban_item_toggle"),
    path("projetos/kanban/item/<int:pk>/excluir/", views.kanban_item_excluir, name="kanban_item_excluir"),
    # Kanban legado (card/coluna)
    path("projetos/card/criar/", views.kanban_card_criar, name="kanban_card_criar"),
    path("projetos/card/<int:pk>/mover/", views.kanban_card_mover, name="kanban_card_mover"),
    path("projetos/coluna/criar/", views.kanban_coluna_criar, name="kanban_coluna_criar"),
    path("projetos/coluna/<int:pk>/editar/", views.kanban_coluna_editar, name="kanban_coluna_editar"),
    path("projetos/coluna/<int:pk>/excluir/", views.kanban_coluna_excluir, name="kanban_coluna_excluir"),
    path("projetos/colunas/reordenar/", views.kanban_colunas_reordenar, name="kanban_colunas_reordenar"),
    # Assistente
    path("assistente/", views.assistente, name="assistente_chat"),
    path("assistente/responder/", views.assistente_responder, name="assistente_responder"),
]
