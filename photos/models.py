import uuid
from pathlib import Path

from django.db import models


def private_asset_path(asset, filename):
    extension = Path(filename).suffix.lower()
    return (
        f"albums/{asset.photo.album_id}/photos/{asset.photo_id}/{asset.id}/{asset.kind}{extension}"
    )


class Photo(models.Model):
    class State(models.TextChoices):
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    album = models.ForeignKey("albums.Album", on_delete=models.CASCADE, related_name="photos")
    upload_id = models.UUIDField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    original_filename = models.CharField(max_length=255)
    state = models.CharField(max_length=20, choices=State, default=State.PROCESSING)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "created_at", "id"]
        indexes = [models.Index(fields=["album", "display_order"])]
        constraints = [
            models.UniqueConstraint(
                fields=["album", "upload_id"],
                condition=models.Q(upload_id__isnull=False),
                name="unique_photo_upload_id_per_album",
            )
        ]

    def __str__(self):
        return self.original_filename

    @property
    def preview_asset(self):
        return next(
            (asset for asset in self.assets.all() if asset.kind == asset.Kind.PREVIEW), None
        )

    @property
    def original_asset(self):
        return next(
            (asset for asset in self.assets.all() if asset.kind == asset.Kind.ORIGINAL), None
        )


class PhotoAsset(models.Model):
    class Kind(models.TextChoices):
        ORIGINAL = "original", "Original"
        PREVIEW = "preview", "Preview"
        AI_IMPROVED = "ai_improved", "AI improved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="assets")
    kind = models.CharField(max_length=20, choices=Kind)
    file = models.FileField(upload_to=private_asset_path, max_length=500)
    checksum = models.CharField(max_length=64)
    media_type = models.CharField(max_length=80)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    byte_size = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["photo"],
                condition=models.Q(kind="original"),
                name="one_original_asset_per_photo",
            ),
            models.UniqueConstraint(
                fields=["photo"],
                condition=models.Q(kind="preview"),
                name="one_preview_asset_per_photo",
            ),
        ]

    def __str__(self):
        return f"{self.photo}: {self.get_kind_display()}"


class StoredFileDeletion(models.Model):
    class State(models.TextChoices):
        PENDING = "pending", "Pending"
        FAILED = "failed", "Failed"
        DELETED = "deleted", "Deleted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    storage_key = models.CharField(max_length=500, unique=True)
    state = models.CharField(max_length=20, choices=State, default=State.PENDING)
    attempt_count = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.storage_key}: {self.get_state_display()}"
