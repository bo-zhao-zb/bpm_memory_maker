from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from .models import PrintProduct


class PrintProductTests(TestCase):
    def test_dimensions_must_be_positive(self):
        for dimension in (0, -1):
            with self.subTest(dimension=dimension):
                product = PrintProduct(
                    code="invalid", name="Invalid", width_mm=dimension, height_mm=1
                )
                with self.assertRaises(ValidationError):
                    product.full_clean()

    def test_seed_is_repeatable_and_preserves_admin_changes(self):
        call_command("seed_catalog", stdout=StringIO())
        self.assertEqual(PrintProduct.objects.count(), 4)
        PrintProduct.objects.filter(code="6x4").update(name="Custom name", active=False)
        call_command("seed_catalog", stdout=StringIO())
        self.assertEqual(PrintProduct.objects.count(), 4)
        product = PrintProduct.objects.get(code="6x4")
        self.assertEqual(product.name, "Custom name")
        self.assertFalse(product.active)
