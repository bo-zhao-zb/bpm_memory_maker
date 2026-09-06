from django.conf import settings
from django.contrib.auth.views import LoginView
from django.http import HttpResponseNotAllowed


class SignInView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "development_login": settings.DEBUG,
            "providers": settings.SOCIALACCOUNT_PROVIDERS,
        }

    def post(self, request, *args, **kwargs):
        if not settings.DEBUG:
            return HttpResponseNotAllowed(["GET", "HEAD", "OPTIONS"])
        return super().post(request, *args, **kwargs)
