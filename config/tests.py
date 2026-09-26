from unittest.mock import patch

from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse


class HealthTests(SimpleTestCase):
    @override_settings(APP_RELEASE="test-release")
    def test_health_is_public_and_does_not_require_database(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "release": "test-release"})

    def test_health_rejects_post(self):
        self.assertEqual(self.client.post(reverse("health")).status_code, 405)


class ReadinessTests(TestCase):
    @override_settings(APP_RELEASE="test-release")
    def test_readiness_checks_database(self):
        response = self.client.get(reverse("readiness"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "release": "test-release"})

    def test_readiness_reports_database_failure_without_details(self):
        with patch("config.urls.connection.cursor", side_effect=DatabaseError):
            response = self.client.get(reverse("readiness"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})

    def test_readiness_rejects_post(self):
        self.assertEqual(self.client.post(reverse("readiness")).status_code, 405)
