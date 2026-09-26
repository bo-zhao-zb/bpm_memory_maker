from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp
from django.http import Http404


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_app(self, request, provider, client_id=None):
        try:
            return super().get_app(request, provider, client_id)
        except SocialApp.DoesNotExist as error:
            raise Http404("Social sign-in provider is not configured.") from error
