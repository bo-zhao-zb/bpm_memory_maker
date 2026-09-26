from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.http import require_safe

from accounts.views import SignInView


@require_safe
def health(request):
    return JsonResponse({"status": "ok", "release": settings.APP_RELEASE})


@require_safe
def readiness(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready", "release": settings.APP_RELEASE})


urlpatterns = [
    path("", include("albums.urls")),
    path("", include("photos.urls")),
    path("accounts/login/", SignInView.as_view(), name="account_login"),
    path("accounts/logout/", LogoutView.as_view(), name="account_logout"),
    path("accounts/", include("allauth.urls")),
    path("health/", health, name="health"),
    path("ready/", readiness, name="readiness"),
    path("admin/", admin.site.urls),
]
