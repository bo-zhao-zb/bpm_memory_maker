from django.core.management.base import BaseCommand

from catalog.models import PrintProduct


class Command(BaseCommand):
    help = "Add the four planned print sizes without modifying existing catalogue entries."

    def handle(self, *args, **options):
        products = [
            ("6x4", "6 x 4 in", "152.40", "101.60"),
            ("7x5", "7 x 5 in", "177.80", "127.00"),
            ("8x6", "8 x 6 in", "203.20", "152.40"),
            ("10x8", "10 x 8 in", "254.00", "203.20"),
        ]
        created_count = 0
        for position, (code, name, width, height) in enumerate(products):
            _, created = PrintProduct.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "width_mm": width,
                    "height_mm": height,
                    "display_order": position,
                },
            )
            created_count += int(created)
        self.stdout.write(self.style.SUCCESS(f"Added {created_count} print sizes."))
