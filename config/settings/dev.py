from .base import *

DEBUG = True
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-only-change-me")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,10.10.100.169").split(",")
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
