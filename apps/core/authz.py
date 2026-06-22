import logging
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


def tier_required(*tiers):
    """
    Restringe o acesso a usuários que pertençam a pelo menos um dos tiers informados.
    Tiers são nomes de grupos (case-insensitive). superuser sempre tem acesso.
    Ex.: @tier_required("colaborador", "suporte", "admin")
    """
    allowed = {t.lower() for t in tiers}

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                logger.warning("Acesso anônimo negado para path=%s", request.path)
                return redirect_to_login(request.get_full_path())

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            user_tiers = {g.name.lower() for g in request.user.groups.all()}
            if user_tiers & allowed:
                return view_func(request, *args, **kwargs)

            logger.warning(
                "Acesso negado para user=%s path=%s tiers_user=%s tiers_required=%s",
                request.user.username, request.path, user_tiers, allowed,
            )
            raise PermissionDenied("Sem permissão para acessar esta página.")
        return _wrapped
    return decorator
