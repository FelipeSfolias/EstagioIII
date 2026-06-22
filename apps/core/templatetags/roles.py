from django import template

register = template.Library()


@register.filter
def has_group(user, group_name: str) -> bool:
    """Retorna True se o usuário pertence ao grupo dado (case-insensitive).

    Uso no template: {% if user|has_group:'suporte' %}
    Retorna False para usuários não-autenticados.
    """
    if not getattr(user, "is_authenticated", False):
        return False
    return user.groups.filter(name__iexact=group_name).exists()
