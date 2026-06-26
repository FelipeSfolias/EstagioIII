from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-reset/", views.password_reset_start, name="password_reset_start"),
    path("password-reset/confirm/<uuid:token>/", views.password_reset_confirm, name="password_reset_confirm"),
]
