from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.http import require_safe

from accounts.views import SignInView


@require_safe
def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", include("albums.urls")),
    path("accounts/login/", SignInView.as_view(), name="account_login"),
    path("accounts/logout/", LogoutView.as_view(), name="account_logout"),
    path("accounts/", include("allauth.urls")),
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
]
