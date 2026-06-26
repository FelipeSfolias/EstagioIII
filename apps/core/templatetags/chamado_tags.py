import os
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

STATUS_COLOR = {
    "aberto":          "blue",
    "em_atendimento":  "yellow",
    "resolvido":       "green",
    "fechado":         "gray",
}

PRIORIDADE_COLOR = {
    "alta":  "red",
    "media": "yellow",
    "baixa": "green",
}

EVENTO_BG = {
    "status":     "var(--blue-light)",
    "prioridade": "var(--yellow-light)",
    "atribuicao": "var(--purple-light)",
    "comentario": "var(--green-light)",
}

EVENTO_ICON_SVG = {
    "status": '<svg width="13" height="13" viewBox="0 0 16 16" fill="none">'
              '<circle cx="8" cy="8" r="5" stroke="#2563eb" stroke-width="1.8"/>'
              '<path d="M8 5v3l2 1" stroke="#2563eb" stroke-width="1.5" stroke-linecap="round"/>'
              '</svg>',
    "prioridade": '<svg width="13" height="13" viewBox="0 0 16 16" fill="none">'
                  '<path d="M8 2l1.8 3.6L14 6.5l-3 2.9.7 4.1L8 11.4l-3.7 1.9.7-4.1L2 6.5l4.2-.9L8 2z"'
                  ' stroke="#ca8a04" stroke-width="1.5" stroke-linejoin="round"/>'
                  '</svg>',
    "atribuicao": '<svg width="13" height="13" viewBox="0 0 16 16" fill="none">'
                  '<circle cx="8" cy="5" r="2.5" stroke="#7c3aed" stroke-width="1.5"/>'
                  '<path d="M3 13c0-2.76 2.24-5 5-5s5 2.24 5 5" stroke="#7c3aed" stroke-width="1.5" stroke-linecap="round"/>'
                  '</svg>',
    "comentario": '<svg width="13" height="13" viewBox="0 0 16 16" fill="none">'
                  '<path d="M2 3h12v8H9l-3 3v-3H2V3z" stroke="#16a34a" stroke-width="1.5" stroke-linejoin="round"/>'
                  '</svg>',
}


@register.filter
def status_color(value):
    return STATUS_COLOR.get(str(value).lower(), "gray")


@register.filter
def prioridade_color(value):
    return PRIORIDADE_COLOR.get(str(value).lower(), "gray")


@register.filter
def evento_bg_color(value):
    return EVENTO_BG.get(str(value).lower(), "#f3f4f6")


@register.filter(is_safe=True)
def evento_icon(value):
    return mark_safe(EVENTO_ICON_SVG.get(str(value).lower(), ""))


@register.filter
def filename(value):
    return os.path.basename(str(value))


@register.filter
def user_initials(user):
    """Returns 1-2 letter initials from a User object or full-name string."""
    if not user:
        return '?'
    try:
        full = (user.get_full_name() or user.username or '').strip()
    except AttributeError:
        full = str(user).strip()
    parts = full.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return (full[:2] or '??').upper()


@register.simple_tag(takes_context=True)
def url_filtro(context, reset_page=True, **kwargs):
    """Reescreve a query string atual aplicando/limpando params.

    Valor vazio (ou '__none__') remove o param. Por padrão zera 'page'
    (use reset_page=False na paginação para preservar a página alvo).
    """
    params = context["request"].GET.copy()
    for k, v in kwargs.items():
        if v in (None, "", "__none__"):
            params.pop(k, None)
        else:
            params[k] = v
    if reset_page:
        params.pop("page", None)
    qs = params.urlencode()
    return ("?" + qs) if qs else "?"
