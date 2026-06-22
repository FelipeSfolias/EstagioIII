import logging
import secrets
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.shortcuts import render, redirect

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        resp = super().form_valid(form)
        if self.request.POST.get("remember_me"):
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            self.request.session.set_expiry(0)
        return resp


def password_reset_start(request):
    if request.method == "POST":
        ip = (
            request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
            .split(",")[0]
            .strip()
        )
        rate_key = f"pwd_reset_rate:{ip}"
        count = cache.get(rate_key, 0)
        if count >= 5:
            messages.error(request, "Muitas tentativas. Aguarde 15 minutos e tente novamente.")
            return render(request, "registration/password_reset_start.html")
        cache.set(rate_key, count + 1, 900)

        email = request.POST.get("email", "").strip()
        code = f"{secrets.randbelow(1_000_000):06d}"
        request.session["pwd_reset_email"] = email
        request.session["pwd_reset_code"] = code
        request.session["pwd_reset_expires"] = time.time() + 600
        request.session["pwd_reset_attempts"] = 0
        logger.info("Solicitação de reset para email=%s ip=%s", email, ip)
        messages.info(request, "Enviamos um código de verificação para seu e-mail.")
        return redirect("accounts:password_reset_code")
    return render(request, "registration/password_reset_start.html")


_RESET_SESSION_KEYS = (
    "pwd_reset_email", "pwd_reset_code", "pwd_reset_expires", "pwd_reset_attempts",
)


def _clear_reset_session(session):
    for k in _RESET_SESSION_KEYS:
        session.pop(k, None)


def password_reset_code(request):
    # Bloquear sessões com excesso de tentativas antes de qualquer outra verificação
    blocked_until = request.session.get("pwd_reset_blocked_until", 0)
    if time.time() < float(blocked_until):
        remaining = max(int((float(blocked_until) - time.time()) / 60) + 1, 1)
        messages.error(request, f"Muitas tentativas incorretas. Aguarde {remaining} minuto(s).")
        return redirect("accounts:password_reset_start")

    email = request.session.get("pwd_reset_email")
    code_expected = request.session.get("pwd_reset_code")
    expires = request.session.get("pwd_reset_expires", 0)

    if not email or not code_expected:
        messages.error(request, "Sessão expirada. Solicite novamente.")
        return redirect("accounts:password_reset_start")

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        p1 = request.POST.get("password1", "")
        p2 = request.POST.get("password2", "")

        if time.time() > float(expires):
            messages.error(request, "Código expirado. Solicite novamente.")
            _clear_reset_session(request.session)
            return redirect("accounts:password_reset_start")

        if code != code_expected:
            attempts = request.session.get("pwd_reset_attempts", 0) + 1
            request.session["pwd_reset_attempts"] = attempts
            if attempts >= 5:
                request.session["pwd_reset_blocked_until"] = time.time() + 900
                _clear_reset_session(request.session)
                messages.error(request, "Muitas tentativas incorretas. Aguarde 15 minutos.")
                return redirect("accounts:password_reset_start")
            messages.error(request, "Código inválido.")
            return render(request, "registration/password_reset_code.html")

        if not p1 or p1 != p2:
            messages.error(request, "As senhas não conferem.")
            return render(request, "registration/password_reset_code.html")

        user = User.objects.filter(email__iexact=email).first()
        _clear_reset_session(request.session)
        if user:
            user.set_password(p1)
            user.save()
        # Mesma mensagem em ambos os casos para não revelar se e-mail existe
        messages.info(request, "Se o e-mail estiver cadastrado, a senha foi redefinida.")
        return redirect("accounts:login")

    return render(request, "registration/password_reset_code.html")


@login_required
def pos_login_redirect(request):
    u = request.user
    if u.is_superuser or u.groups.filter(name__iexact="admin").exists():
        return redirect("core:dashboard")
    if u.groups.filter(name__iexact="suporte").exists():
        return redirect("core:chamados_indicadores")
    if u.groups.filter(name__iexact="colaborador").exists():
        return redirect("core:chamado_criar_tier")
    return redirect("core:chamado_criar_tier")
