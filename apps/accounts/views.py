import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import PasswordResetToken

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
        logger.info("Solicitação de reset para email=%s ip=%s", email, ip)

        user = User.objects.filter(email__iexact=email).first()
        if user:
            token_obj = PasswordResetToken.create_for_user(user)
            reset_url = request.build_absolute_uri(
                reverse("accounts:password_reset_confirm", kwargs={"token": token_obj.token})
            )
            try:
                send_mail(
                    subject="Recuperação de senha — SIGCPC",
                    message=(
                        f"Olá, {user.get_full_name() or user.username}!\n\n"
                        f"Recebemos uma solicitação para redefinir a senha da sua conta.\n\n"
                        f"Clique no link abaixo para criar uma nova senha:\n{reset_url}\n\n"
                        f"Este link expira em 1 hora. Após isso, solicite um novo link.\n\n"
                        f"Se você não solicitou a recuperação de senha, ignore este e-mail."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                logger.info("E-mail de reset enviado para %s", email)
            except Exception as exc:
                logger.error("Falha ao enviar e-mail de reset para %s: %s", email, exc)
                messages.error(request, "Erro ao enviar o e-mail. Tente novamente mais tarde.")
                return render(request, "registration/password_reset_start.html")

        # Mesma mensagem com ou sem usuário cadastrado (evita enumeração de e-mails)
        messages.info(request, "Se o e-mail estiver cadastrado, você receberá um link em instantes.")
        return redirect("accounts:password_reset_start")

    return render(request, "registration/password_reset_start.html")


def password_reset_confirm(request, token):
    token_obj = PasswordResetToken.objects.select_related("user").filter(token=token).first()

    if not token_obj or not token_obj.is_valid():
        messages.error(request, "Link inválido ou expirado. Solicite um novo link de recuperação.")
        return redirect("accounts:password_reset_start")

    if request.method == "POST":
        p1 = request.POST.get("password1", "")
        p2 = request.POST.get("password2", "")

        if len(p1) < 8:
            messages.error(request, "A senha deve ter pelo menos 8 caracteres.")
            return render(request, "registration/password_reset_confirm.html", {"token": token})

        if p1 != p2:
            messages.error(request, "As senhas não conferem.")
            return render(request, "registration/password_reset_confirm.html", {"token": token})

        user = token_obj.user
        user.set_password(p1)
        user.save()
        token_obj.used = True
        token_obj.save(update_fields=["used"])
        logger.info("Senha redefinida com sucesso para user=%s", user.username)

        messages.info(request, "Senha redefinida com sucesso! Faça login com a nova senha.")
        return redirect("accounts:login")

    return render(request, "registration/password_reset_confirm.html", {"token": token})


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
