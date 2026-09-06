from django.db import models


class PrintProduct(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    width_mm = models.DecimalField(max_digits=7, decimal_places=2)
    height_mm = models.DecimalField(max_digits=7, decimal_places=2)
    active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(width_mm__gt=0, height_mm__gt=0),
                name="print_product_positive_dimensions",
            ),
        ]

    def __str__(self):
        return self.name
