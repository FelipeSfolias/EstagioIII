from rest_framework.routers import DefaultRouter

from .api_views import (
    AtivoViewSet,
    ChamadoViewSet,
    ItemEstoqueViewSet,
    KanbanCardViewSet,
    LocalViewSet,
    UsuarioViewSet,
)

router = DefaultRouter()
router.register("locais", LocalViewSet, basename="local")
router.register("ativos", AtivoViewSet, basename="ativo")
router.register("itens-estoque", ItemEstoqueViewSet, basename="itemestoque")
router.register("chamados", ChamadoViewSet, basename="chamado")
router.register("projetos", KanbanCardViewSet, basename="projeto")
router.register("usuarios", UsuarioViewSet, basename="usuario")

urlpatterns = router.urls
