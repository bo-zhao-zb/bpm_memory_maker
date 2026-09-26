from django.core.management.base import BaseCommand

from photos.services import process_file_deletions


class Command(BaseCommand):
    help = "Retry pending or failed private-file deletions."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        limit = options["limit"]
        if limit < 1:
            self.stderr.write(self.style.ERROR("Limit must be a positive integer."))
            return
        deleted, failed = process_file_deletions(limit=limit)
        self.stdout.write(f"Deleted {deleted} file(s); {failed} deletion(s) still failing.")
