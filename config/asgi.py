import os

from django.core.asgi import get_asgi_application

django_env = os.getenv("DJANGO_ENV", "local").strip() or "local"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{django_env}")

application = get_asgi_application()
