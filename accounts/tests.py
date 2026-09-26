from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


class SignInTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="tester", password="test-password-not-a-real-secret"
        )

    @override_settings(DEBUG=True)
    def test_login_has_local_assets_and_progressive_password_control(self):
        response = self.client.get(reverse("account_login"))
        self.assertContains(response, 'src="/static/js/ui.js"')
        self.assertContains(response, 'src="/static/vendor/memory-mountains.jpg"')
        self.assertContains(response, 'type="password"')
        self.assertContains(response, 'aria-controls="id_password"')
        self.assertRegex(
            response.content.decode(), r"<button[^>]*data-password-toggle[^>]* hidden>"
        )

    @override_settings(DEBUG=True)
    def test_invalid_login_keeps_feedback_without_echoing_password(self):
        response = self.client.post(
            reverse("account_login"),
            {"username": "tester", "password": "deliberately-incorrect-ui-test"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertContains(response, 'role="alert"')
        self.assertNotContains(response, "deliberately-incorrect-ui-test")
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(DEBUG=True)
    def test_development_login_and_post_logout(self):
        response = self.client.post(
            reverse("account_login"),
            {"username": "tester", "password": "test-password-not-a-real-secret"},
        )
        self.assertRedirects(response, reverse("albums:list"))
        self.assertEqual(self.client.get(reverse("account_logout")).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
        self.client.post(reverse("account_logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(DEBUG=True)
    def test_development_login_rejects_external_next_url(self):
        response = self.client.post(
            reverse("account_login"),
            {
                "username": "tester",
                "password": "test-password-not-a-real-secret",
                "next": "https://untrusted.example/",
            },
        )
        self.assertRedirects(response, reverse("albums:list"))

    @override_settings(DEBUG=False)
    def test_password_login_is_disabled_outside_development(self):
        response = self.client.post(
            reverse("account_login"),
            {"username": "tester", "password": "test-password-not-a-real-secret"},
        )
        self.assertEqual(response.status_code, 405)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotContains(self.client.get(reverse("account_login")), 'name="password"')

    @override_settings(DEBUG=True)
    def test_inactive_user_cannot_sign_in(self):
        self.user.is_active = False
        self.user.save()
        self.client.post(
            reverse("account_login"),
            {"username": "tester", "password": "test-password-not-a-real-secret"},
        )
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(SOCIALACCOUNT_PROVIDERS={})
    def test_unconfigured_provider_routes_return_not_found(self):
        response = self.client.get(reverse("account_login"))
        self.assertNotContains(response, "Continue with Google")
        self.assertNotContains(response, "Continue with Facebook")
        for provider in ("google", "facebook"):
            with self.subTest(provider=provider, method="get"):
                self.assertEqual(self.client.get(reverse(f"{provider}_login")).status_code, 404)
            with self.subTest(provider=provider, method="post"):
                self.assertEqual(self.client.post(reverse(f"{provider}_login")).status_code, 404)

    @override_settings(
        SOCIALACCOUNT_PROVIDERS={
            "google": {"APPS": [{"client_id": "test-id", "secret": "test-secret", "key": ""}]},
            "facebook": {"APPS": [{"client_id": "test-id", "secret": "test-secret", "key": ""}]},
        }
    )
    def test_configured_providers_are_visible_and_begin_oauth(self):
        response = self.client.get(reverse("account_login"))
        self.assertContains(response, "Continue with Google")
        self.assertContains(response, "Continue with Facebook")
        for provider, host in (("google", "accounts.google.com"), ("facebook", "facebook.com")):
            with self.subTest(provider=provider):
                response = self.client.post(reverse(f"{provider}_login"))
                self.assertEqual(response.status_code, 302)
                self.assertIn(host, response.url)
                self.assertIn("state=", response.url)
