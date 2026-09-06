from django.core.exceptions import ValidationError
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
