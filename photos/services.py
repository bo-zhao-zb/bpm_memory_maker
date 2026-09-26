import hashlib
import uuid
import warnings
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import F, Max
from django.utils import timezone
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from albums.models import Album, draft_expiry

from .models import Photo, PhotoAsset, StoredFileDeletion

register_heif_opener()

FORMAT_DETAILS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "HEIF": ("image/heic", ".heic"),
}


class PhotoUploadRejected(Exception):
    def __init__(self, message, *, code):
        super().__init__(message)
        self.code = code


class PhotoAlbumReadOnly(Exception):
    pass


class AlbumCapacityReached(Exception):
    pass


class PhotoConflict(Exception):
    pass


@dataclass(frozen=True)
class PreparedPhoto:
    original_filename: str
    media_type: str
    extension: str
    width: int
    height: int
    byte_size: int
    checksum: str
    preview: bytes
    preview_width: int
    preview_height: int


def _require_owner(owner):
    if not owner.is_authenticated or not owner.is_active:
        raise PermissionDenied


def _display_filename(uploaded_file):
    name = Path(uploaded_file.name or "photo").name.strip() or "photo"
    return name[:255]


def _checksum(uploaded_file):
    uploaded_file.seek(0)
    digest = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        digest.update(chunk)
    uploaded_file.seek(0)
    return digest.hexdigest()


def _rgb_image(image):
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def _apply_orientation(image):
    original_orientation = image.info.get("original_orientation")
    if not original_orientation:
        return ImageOps.exif_transpose(image)
    transforms = {
        2: Image.Transpose.FLIP_LEFT_RIGHT,
        3: Image.Transpose.ROTATE_180,
        4: Image.Transpose.FLIP_TOP_BOTTOM,
        5: Image.Transpose.TRANSPOSE,
        6: Image.Transpose.ROTATE_270,
        7: Image.Transpose.TRANSVERSE,
        8: Image.Transpose.ROTATE_90,
    }
    transform = transforms.get(original_orientation)
    return image.transpose(transform) if transform else image.copy()


def prepare_photo(uploaded_file):
    byte_size = uploaded_file.size
    if byte_size > settings.PHOTO_MAX_FILE_SIZE:
        raise PhotoUploadRejected(
            "This file is larger than the upload limit.", code="file_too_large"
        )

    try:
        uploaded_file.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(uploaded_file) as source:
                image_format = source.format
                if image_format not in FORMAT_DETAILS:
                    raise PhotoUploadRejected(
                        "Choose a JPEG, PNG, HEIC or HEIF image.", code="unsupported_format"
                    )
                if source.width * source.height > settings.PHOTO_MAX_PIXELS:
                    raise PhotoUploadRejected(
                        "This image has too many pixels to process safely.", code="too_many_pixels"
                    )
                source.load()
                oriented = _apply_orientation(source)
                width, height = oriented.size
                preview = _rgb_image(oriented)
    except PhotoUploadRejected:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise PhotoUploadRejected(
            "This image has too many pixels to process safely.", code="too_many_pixels"
        ) from None
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise PhotoUploadRejected(
            "This file is not a readable supported image.", code="invalid_image"
        ) from None

    preview.thumbnail(
        (settings.PHOTO_PREVIEW_MAX_DIMENSION, settings.PHOTO_PREVIEW_MAX_DIMENSION),
        Image.Resampling.LANCZOS,
    )
    preview_output = BytesIO()
    preview.save(
        preview_output,
        format="JPEG",
        quality=settings.PHOTO_PREVIEW_JPEG_QUALITY,
        optimize=True,
    )
    media_type, extension = FORMAT_DETAILS[image_format]
    return PreparedPhoto(
        original_filename=_display_filename(uploaded_file),
        media_type=media_type,
        extension=extension,
        width=width,
        height=height,
        byte_size=byte_size,
        checksum=_checksum(uploaded_file),
        preview=preview_output.getvalue(),
        preview_width=preview.width,
        preview_height=preview.height,
    )


def _classify_album_change(album):
    album.refresh_from_db()
    if not album.is_editable:
        raise PhotoAlbumReadOnly("This album is no longer an editable draft.")
    if album.photo_count >= album.photo_limit:
        raise AlbumCapacityReached("This album has reached its photo limit.")
    raise AlbumCapacityReached("A photo slot could not be reserved. Try again.")


def create_photo(*, owner, album_id, uploaded_file, upload_id=None):
    _require_owner(owner)
    album = Album.objects.get(pk=album_id, owner=owner)
    if upload_id:
        upload_id = uuid.UUID(str(upload_id))
        existing = Photo.objects.filter(album=album, upload_id=upload_id).first()
        if existing:
            return existing
    if not album.is_editable:
        raise PhotoAlbumReadOnly("This album is no longer an editable draft.")
    if album.photo_count >= album.photo_limit:
        raise AlbumCapacityReached("This album has reached its photo limit.")
    prepared = prepare_photo(uploaded_file)

    saved_files = []
    photo = None
    try:
        with transaction.atomic():
            reserved = Album.objects.filter(
                pk=album.pk,
                owner=owner,
                state=Album.State.DRAFT,
                expires_at__gt=timezone.now(),
                photo_count__lt=F("photo_limit"),
            ).update(
                photo_count=F("photo_count") + 1,
                version=F("version") + 1,
                updated_at=timezone.now(),
                expires_at=draft_expiry(),
            )
            if not reserved:
                _classify_album_change(album)

            display_order = (
                Photo.objects.filter(album=album).aggregate(maximum=Max("display_order"))["maximum"]
                or 0
            ) + 1
            photo = Photo.objects.create(
                album=album,
                upload_id=upload_id,
                display_order=display_order,
                original_filename=prepared.original_filename,
                state=Photo.State.PROCESSING,
                width=prepared.width,
                height=prepared.height,
            )

        uploaded_file.seek(0)
        original = PhotoAsset(
            photo=photo,
            kind=PhotoAsset.Kind.ORIGINAL,
            checksum=prepared.checksum,
            media_type=prepared.media_type,
            width=prepared.width,
            height=prepared.height,
            byte_size=prepared.byte_size,
        )
        original.file.save(f"original{prepared.extension}", uploaded_file, save=False)
        saved_files.append(original.file.name)
        original.save()

        preview_content = ContentFile(prepared.preview)
        preview = PhotoAsset(
            photo=photo,
            kind=PhotoAsset.Kind.PREVIEW,
            checksum=hashlib.sha256(prepared.preview).hexdigest(),
            media_type="image/jpeg",
            width=prepared.preview_width,
            height=prepared.preview_height,
            byte_size=len(prepared.preview),
        )
        preview.file.save("preview.jpg", preview_content, save=False)
        saved_files.append(preview.file.name)
        preview.save()

        photo.state = Photo.State.READY
        photo.save(update_fields=["state", "updated_at"])
    except Exception:
        if photo is not None and Photo.objects.filter(pk=photo.pk).exists():
            with transaction.atomic():
                photo.delete()
                Album.objects.filter(
                    pk=album.pk,
                    owner=owner,
                    photo_count__gt=0,
                ).update(
                    photo_count=F("photo_count") - 1,
                    version=F("version") + 1,
                    updated_at=timezone.now(),
                )
        schedule_file_deletions(saved_files)
        raise

    photo.refresh_from_db()
    return photo


def delete_photo(*, owner, photo_id, expected_album_version):
    _require_owner(owner)
    photo = (
        Photo.objects.select_related("album")
        .prefetch_related("assets")
        .get(pk=photo_id, album__owner=owner)
    )
    if not photo.album.is_editable:
        raise PhotoAlbumReadOnly("This album is no longer an editable draft.")
    if photo.album.version != expected_album_version:
        raise PhotoConflict("This album changed in another session. Reload it before trying again.")
    stored_names = [asset.file.name for asset in photo.assets.all()]

    with transaction.atomic():
        updated = Album.objects.filter(
            pk=photo.album_id,
            owner=owner,
            state=Album.State.DRAFT,
            version=expected_album_version,
            expires_at__gt=timezone.now(),
            photo_count__gt=0,
        ).update(
            photo_count=F("photo_count") - 1,
            version=F("version") + 1,
            updated_at=timezone.now(),
            expires_at=draft_expiry(),
        )
        if not updated:
            photo.album.refresh_from_db()
            if not photo.album.is_editable:
                raise PhotoAlbumReadOnly("This album is no longer an editable draft.")
            raise PhotoConflict(
                "This album changed in another session. Reload it before trying again."
            )
        deletion_ids = queue_file_deletions(stored_names)
        photo.delete()
        transaction.on_commit(lambda: process_file_deletions(ids=deletion_ids))


def queue_file_deletions(names):
    keys = list(dict.fromkeys(name for name in names if name))
    StoredFileDeletion.objects.bulk_create(
        [StoredFileDeletion(storage_key=key) for key in keys],
        ignore_conflicts=True,
    )
    return list(
        StoredFileDeletion.objects.filter(storage_key__in=keys).values_list("id", flat=True)
    )


def process_file_deletions(*, ids=None, limit=100):
    pending = StoredFileDeletion.objects.exclude(state=StoredFileDeletion.State.DELETED)
    if ids is not None:
        pending = pending.filter(pk__in=ids)
    deleted = 0
    failed = 0
    for item in pending.order_by("created_at")[:limit]:
        try:
            default_storage.delete(item.storage_key)
        except Exception as error:
            item.state = StoredFileDeletion.State.FAILED
            item.last_error = str(error)[:500]
            failed += 1
        else:
            item.state = StoredFileDeletion.State.DELETED
            item.last_error = ""
            item.completed_at = timezone.now()
            deleted += 1
        item.attempt_count += 1
        item.save(
            update_fields=["state", "last_error", "completed_at", "attempt_count", "updated_at"]
        )
    return deleted, failed


def schedule_file_deletions(names):
    ids = queue_file_deletions(names)
    process_file_deletions(ids=ids)
