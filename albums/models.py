import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


def default_photo_limit():
    return settings.ALBUM_PHOTO_LIMIT


def draft_expiry():
    return timezone.now() + timedelta(days=settings.DRAFT_RETENTION_DAYS)


class Album(models.Model):
    class State(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        IN_PRODUCTION = "in_production", "In production"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=20, choices=State, default=State.DRAFT)
    default_print_product = models.ForeignKey("catalog.PrintProduct", on_delete=models.PROTECT)
    photo_limit = models.PositiveIntegerField(
        default=default_photo_limit, validators=[MinValueValidator(1)]
    )
    photo_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(default=draft_expiry)
    version = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-updated_at", "-created_at", "id"]
        indexes = [models.Index(fields=["owner", "-updated_at"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(photo_limit__gt=0), name="album_positive_limit"
            ),
            models.CheckConstraint(
                condition=models.Q(version__gt=0), name="album_positive_version"
            ),
            models.CheckConstraint(
                condition=models.Q(photo_count__lte=models.F("photo_limit")),
                name="album_photo_count_within_limit",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "Enter an album name."})

    @property
    def is_editable(self):
        return self.state == self.State.DRAFT and self.expires_at > timezone.now()

    def get_absolute_url(self):
        return reverse("albums:detail", kwargs={"album_id": self.pk})
