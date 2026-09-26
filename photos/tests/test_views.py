from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from albums.services import create_album, delete_album
from catalog.models import PrintProduct
from photos.models import Photo
from photos.services import create_photo

from .test_services import image_upload


class PhotoViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="view-owner")
        cls.other = get_user_model().objects.create_user(username="view-other")
        cls.product = PrintProduct.objects.create(
            code="view-6x4",
            name="View 6 x 4 in",
            width_mm="152.40",
            height_mm="101.60",
        )

    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        self.album = create_album(
            owner=self.owner,
            name="Private gallery",
            default_print_product=self.product,
        )
        self.client.force_login(self.owner)

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def upload_url(self):
        return reverse("photos:upload", args=[self.album.pk])

    def test_json_upload_returns_created_photo_and_detail_renders_private_preview(self):
        upload, _ = image_upload(name="family photo.jpg")
        response = self.client.post(
            self.upload_url(),
            {"photos": upload},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["errors"], [])
        photo = Photo.objects.get(pk=response.json()["created"][0]["id"])
        detail = self.client.get(self.album.get_absolute_url())
        self.assertContains(detail, "family photo.jpg")
        self.assertContains(detail, "1 of 100")
        self.assertContains(detail, "Remove this photo from the album?")
        self.assertContains(
            detail,
            reverse("photos:asset", args=[photo.preview_asset.pk]),
        )

    def test_multi_file_upload_reports_partial_failure_without_losing_valid_photo(self):
        valid, _ = image_upload(name="valid.jpg")
        invalid = SimpleUploadedFile("broken.jpg", b"not an image")
        response = self.client.post(
            self.upload_url(),
            {"photos": [valid, invalid]},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(response.json()["created"]), 1)
        self.assertEqual(response.json()["errors"][0]["filename"], "broken.jpg")
        self.assertEqual(Photo.objects.filter(album=self.album).count(), 1)

    @override_settings(PHOTO_MAX_FILES_PER_REQUEST=1, DATA_UPLOAD_MAX_NUMBER_FILES=2)
    def test_form_rejects_too_many_files_in_one_request(self):
        first, _ = image_upload(name="first.jpg")
        second, _ = image_upload(name="second.jpg")
        response = self.client.post(
            self.upload_url(),
            {"photos": [first, second]},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["created"], [])
        self.assertEqual(Photo.objects.filter(album=self.album).count(), 0)

    def test_original_is_attachment_and_preview_is_inline_but_both_are_private(self):
        upload, content = image_upload(name='unsafe "name".jpg')
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        original = photo.original_asset
        preview = photo.preview_asset

        response = self.client.get(reverse("photos:asset", args=[original.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(b"".join(response.streaming_content), content)

        response = self.client.get(reverse("photos:asset", args=[preview.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("inline", response["Content-Disposition"])
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_other_user_cannot_upload_read_or_delete(self):
        upload, _ = image_upload()
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        self.client.force_login(self.other)
        other_upload, _ = image_upload()
        self.assertEqual(
            self.client.post(self.upload_url(), {"photos": other_upload}).status_code,
            404,
        )
        for asset in photo.assets.all():
            with self.subTest(asset=asset.kind):
                self.assertEqual(
                    self.client.get(reverse("photos:asset", args=[asset.pk])).status_code,
                    404,
                )
        self.assertEqual(
            self.client.post(
                reverse("photos:delete", args=[photo.pk]),
                {"version": 2},
            ).status_code,
            404,
        )
        self.assertTrue(Photo.objects.filter(pk=photo.pk).exists())

    def test_authentication_and_csrf_are_required(self):
        upload, _ = image_upload()
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        self.client.logout()
        self.assertEqual(self.client.post(self.upload_url()).status_code, 302)
        self.assertEqual(
            self.client.get(reverse("photos:asset", args=[photo.original_asset.pk])).status_code,
            302,
        )

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        fresh_upload, _ = image_upload()
        self.assertEqual(
            client.post(self.upload_url(), {"photos": fresh_upload}).status_code,
            403,
        )
        self.assertEqual(
            client.post(reverse("photos:delete", args=[photo.pk]), {"version": 2}).status_code,
            403,
        )

    def test_get_cannot_upload_or_delete(self):
        upload, _ = image_upload()
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        self.assertEqual(self.client.get(self.upload_url()).status_code, 405)
        self.assertEqual(
            self.client.get(reverse("photos:delete", args=[photo.pk])).status_code,
            405,
        )

    def test_delete_removes_photo_and_files(self):
        upload, _ = image_upload()
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        paths = [Path(asset.file.path) for asset in photo.assets.all()]
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("photos:delete", args=[photo.pk]),
                {"version": 2},
            )
        self.assertRedirects(response, self.album.get_absolute_url())
        self.assertFalse(Photo.objects.filter(pk=photo.pk).exists())
        self.assertTrue(all(not path.exists() for path in paths))

    def test_stale_photo_delete_does_not_change_count(self):
        upload, _ = image_upload()
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        response = self.client.post(
            reverse("photos:delete", args=[photo.pk]),
            {"version": 1},
        )
        self.assertRedirects(response, self.album.get_absolute_url())
        self.assertTrue(Photo.objects.filter(pk=photo.pk).exists())
        self.album.refresh_from_db()
        self.assertEqual(self.album.photo_count, 1)

    def test_missing_delete_version_is_rejected(self):
        upload, _ = image_upload()
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        response = self.client.post(reverse("photos:delete", args=[photo.pk]))
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Photo.objects.filter(pk=photo.pk).exists())

    def test_deleting_album_removes_all_photo_files(self):
        upload, _ = image_upload()
        photo = create_photo(owner=self.owner, album_id=self.album.pk, uploaded_file=upload)
        paths = [Path(asset.file.path) for asset in photo.assets.all()]
        with self.captureOnCommitCallbacks(execute=True):
            delete_album(owner=self.owner, album_id=self.album.pk, expected_version=2)
        self.assertTrue(all(not path.exists() for path in paths))
