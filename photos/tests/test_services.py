import hashlib
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from PIL import Image
from pillow_heif import register_heif_opener

from albums.models import Album
from albums.services import create_album
from catalog.models import PrintProduct
from photos import services
from photos.models import Photo, PhotoAsset
from photos.services import (
    AlbumCapacityReached,
    PhotoAlbumReadOnly,
    PhotoUploadRejected,
    create_photo,
    delete_photo,
)

register_heif_opener()


def image_upload(*, image_format="JPEG", name=None, size=(80, 60), orientation=None):
    output = BytesIO()
    image = Image.new("RGB", size, "#d06d5d")
    save_options = {}
    if orientation:
        exif = Image.Exif()
        exif[274] = orientation
        save_options["exif"] = exif
    image.save(output, format=image_format, **save_options)
    content = output.getvalue()
    extension = {"JPEG": "jpg", "PNG": "png", "HEIF": "heic"}[image_format]
    return SimpleUploadedFile(name or f"photo.{extension}", content), content


class PhotoServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="photo-owner")
        cls.other = get_user_model().objects.create_user(username="photo-other")
        cls.product = PrintProduct.objects.create(
            code="photo-6x4",
            name="Photo 6 x 4 in",
            width_mm="152.40",
            height_mm="101.60",
        )

    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        self.album = create_album(
            owner=self.owner,
            name="Private uploads",
            default_print_product=self.product,
        )

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_supported_formats_preserve_original_and_create_private_jpeg_preview(self):
        expected = {
            "JPEG": ("image/jpeg", ".jpg"),
            "PNG": ("image/png", ".png"),
            "HEIF": ("image/heic", ".heic"),
        }
        for image_format, (media_type, extension) in expected.items():
            with self.subTest(image_format=image_format):
                upload, original_content = image_upload(
                    image_format=image_format,
                    name=f"misleading-{image_format.lower()}.txt",
                )
                photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
                assets = {asset.kind: asset for asset in photo.assets.all()}
                original = assets[PhotoAsset.Kind.ORIGINAL]
                preview = assets[PhotoAsset.Kind.PREVIEW]

                self.assertEqual(photo.state, Photo.State.READY)
                self.assertEqual((photo.width, photo.height), (80, 60))
                self.assertEqual(original.media_type, media_type)
                self.assertTrue(original.file.name.endswith(extension))
                self.assertEqual(original.checksum, hashlib.sha256(original_content).hexdigest())
                with original.file.open("rb") as stored_original:
                    self.assertEqual(stored_original.read(), original_content)
                with preview.file.open("rb") as stored_preview:
                    with Image.open(stored_preview) as preview_image:
                        preview_image.load()
                        self.assertEqual(preview_image.format, "JPEG")
                        self.assertFalse(preview_image.getexif())

        self.album.refresh_from_db()
        self.assertEqual(self.album.photo_count, 3)
        self.assertEqual(self.album.version, 4)

    def test_exif_orientation_is_applied_to_dimensions_and_preview(self):
        upload, _ = image_upload(size=(80, 40), orientation=6)
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        self.assertEqual((photo.width, photo.height), (40, 80))
        self.assertEqual((photo.preview_asset.width, photo.preview_asset.height), (40, 80))

    def test_invalid_image_is_rejected_without_consuming_capacity_or_storage(self):
        upload = SimpleUploadedFile("not-an-image.jpg", b"this is not an image")
        with self.assertRaises(PhotoUploadRejected) as raised:
            create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        self.assertEqual(raised.exception.code, "invalid_image")
        self.album.refresh_from_db()
        self.assertEqual(self.album.photo_count, 0)
        self.assertFalse(any(Path(self.media_directory.name).rglob("*")))

    @override_settings(PHOTO_MAX_FILE_SIZE=10)
    def test_file_size_limit_is_enforced_before_decode(self):
        upload, _ = image_upload()
        with self.assertRaises(PhotoUploadRejected) as raised:
            create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        self.assertEqual(raised.exception.code, "file_too_large")

    @override_settings(PHOTO_MAX_PIXELS=100)
    def test_decoded_pixel_limit_is_enforced(self):
        upload, _ = image_upload(size=(11, 10))
        with self.assertRaises(PhotoUploadRejected) as raised:
            create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        self.assertEqual(raised.exception.code, "too_many_pixels")

    def test_album_capacity_is_reserved(self):
        Album.objects.filter(pk=self.album.pk).update(photo_limit=1)
        first, _ = image_upload(name="first.jpg")
        second, _ = image_upload(name="second.jpg")
        create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=first)
        with self.assertRaises(AlbumCapacityReached):
            create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=second)
        self.album.refresh_from_db()
        self.assertEqual(self.album.photo_count, 1)
        self.assertEqual(Photo.objects.filter(album=self.album).count(), 1)

    def test_anonymous_and_other_users_cannot_upload(self):
        upload, _ = image_upload()
        with self.assertRaises(PermissionDenied):
            create_photo(owner=AnonymousUser(), album_id=self.album.pk, uploaded_file=upload)
        upload.seek(0)
        with self.assertRaises(Album.DoesNotExist):
            create_photo(owner=self.other, album_id=self.album.pk, uploaded_file=upload)

    def test_non_draft_and_expired_albums_cannot_receive_uploads(self):
        upload, _ = image_upload()
        Album.objects.filter(pk=self.album.pk).update(state=Album.State.SUBMITTED)
        with self.assertRaises(PhotoAlbumReadOnly):
            create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        Album.objects.filter(pk=self.album.pk).update(
            state=Album.State.DRAFT,
            expires_at=timezone.now() - timezone.timedelta(seconds=1),
        )
        upload.seek(0)
        with self.assertRaises(PhotoAlbumReadOnly):
            create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)

    def test_delete_updates_capacity_and_removes_files_after_commit(self):
        upload, _ = image_upload()
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        paths = [Path(asset.file.path) for asset in photo.assets.all()]
        self.assertTrue(all(path.exists() for path in paths))

        with self.captureOnCommitCallbacks(execute=True):
            delete_photo(owner=self.owner, photo_id=photo.pk, expected_album_version=2)

        self.album.refresh_from_db()
        self.assertEqual(self.album.photo_count, 0)
        self.assertFalse(Photo.objects.filter(pk=photo.pk).exists())
        self.assertTrue(all(not path.exists() for path in paths))

    def test_other_user_cannot_delete_photo(self):
        upload, _ = image_upload()
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        with self.assertRaises(Photo.DoesNotExist):
            delete_photo(owner=self.other, photo_id=photo.pk, expected_album_version=2)

    def test_storage_failure_rolls_back_database_capacity_and_saved_files(self):
        upload, _ = image_upload()
        storage = PhotoAsset.file.field.storage
        original_save = storage.save
        calls = 0

        def fail_preview_save(name, content, max_length=None):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated preview storage failure")
            return original_save(name, content, max_length=max_length)

        with patch.object(storage, "save", side_effect=fail_preview_save):
            with self.assertRaisesRegex(OSError, "simulated preview storage failure"):
                create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)

        self.album.refresh_from_db()
        self.assertEqual(self.album.photo_count, 0)
        self.assertEqual(Photo.objects.count(), 0)
        self.assertFalse(any(path.is_file() for path in Path(self.media_directory.name).rglob("*")))


class PhotoCapacityConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        self.owner = get_user_model().objects.create_user(username="capacity-owner")
        product = PrintProduct.objects.create(
            code="capacity-6x4",
            name="Capacity 6 x 4 in",
            width_mm="152.40",
            height_mm="101.60",
        )
        self.album = create_album(
            owner=self.owner,
            name="Capacity album",
            default_print_product=product,
        )
        Album.objects.filter(pk=self.album.pk).update(photo_limit=1)

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_simultaneous_uploads_cannot_exceed_album_capacity(self):
        barrier = Barrier(2)
        original_prepare_photo = services.prepare_photo

        def synchronised_prepare_photo(uploaded_file):
            prepared = original_prepare_photo(uploaded_file)
            barrier.wait(timeout=10)
            return prepared

        def upload(name):
            close_old_connections()
            uploaded_file, _ = image_upload(name=name)
            try:
                return create_photo(
                    owner=self.owner,
                    album_id=self.album.pk,
                    uploaded_file=uploaded_file,
                )
            except Exception as error:
                return error
            finally:
                close_old_connections()

        with patch.object(services, "prepare_photo", synchronised_prepare_photo):
            with ThreadPoolExecutor(max_workers=2) as executor:
                outcomes = list(executor.map(upload, ("first.jpg", "second.jpg")))

        self.assertEqual(sum(isinstance(outcome, Photo) for outcome in outcomes), 1, outcomes)
        self.assertEqual(
            sum(isinstance(outcome, AlbumCapacityReached) for outcome in outcomes), 1, outcomes
        )
        self.album.refresh_from_db()
        self.assertEqual(self.album.photo_count, 1)
        self.assertEqual(Photo.objects.filter(album=self.album).count(), 1)
