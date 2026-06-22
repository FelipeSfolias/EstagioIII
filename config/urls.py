from django.contrib import admin
from django.urls import include, path

from apps.accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("pos-login/", accounts_views.pos_login_redirect, name="pos_login"),
    path("api/", include("apps.core.api_urls")),
    path("", include("apps.core.urls")),
]
