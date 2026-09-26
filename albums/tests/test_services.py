from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from albums import services
from albums.models import Album
from albums.services import AlbumConflict, AlbumReadOnly, create_album, delete_album, update_album
from catalog.models import PrintProduct


class AlbumServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="owner")
        cls.other = get_user_model().objects.create_user(username="other")
        cls.product = PrintProduct.objects.create(
            code="6x4", name="6 x 4 in", width_mm="152.40", height_mm="101.60"
        )
        cls.inactive = PrintProduct.objects.create(
            code="7x5", name="7 x 5 in", width_mm="177.80", height_mm="127.00", active=False
        )

    def setUp(self):
        self.album = create_album(
            owner=self.owner, name="Our summer", default_print_product=self.product
        )

    def update(self, **overrides):
        arguments = {
            "owner": self.owner,
            "album_id": self.album.pk,
            "expected_version": self.album.version,
            "name": "A new name",
            "default_print_product": self.product,
        }
        return update_album(**(arguments | overrides))

    @override_settings(ALBUM_PHOTO_LIMIT=50, DRAFT_RETENTION_DAYS=14)
    def test_creation_uses_configured_limits_and_trims_name(self):
        before = timezone.now()
        album = create_album(
            owner=self.owner, name="  Holiday  ", default_print_product=self.product
        )
        self.assertEqual(album.name, "Holiday")
        self.assertEqual(album.owner, self.owner)
        self.assertEqual(album.state, Album.State.DRAFT)
        self.assertEqual(album.photo_limit, 50)
        self.assertGreaterEqual(album.expires_at, before + timedelta(days=14))

    def test_anonymous_cannot_create(self):
        with self.assertRaises(PermissionDenied):
            create_album(owner=AnonymousUser(), name="No", default_print_product=self.product)

    def test_inactive_user_cannot_mutate(self):
        self.owner.is_active = False
        with self.assertRaises(PermissionDenied):
            self.update()

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.update(name="   ")
        self.album.refresh_from_db()
        self.assertEqual(self.album.name, "Our summer")

    def test_update_increments_version_and_renews_expiry(self):
        updated = self.update()
        self.assertEqual(updated.name, "A new name")
        self.assertEqual(updated.version, 2)
        self.assertGreater(updated.expires_at, self.album.expires_at)

    def test_stale_update_does_not_overwrite(self):
        self.update(name="First edit")
        with self.assertRaises(AlbumConflict):
            self.update(name="Stale edit")
        self.album.refresh_from_db()
        self.assertEqual(self.album.name, "First edit")

    def test_stale_delete_does_not_remove_album(self):
        self.update()
        with self.assertRaises(AlbumConflict):
            delete_album(owner=self.owner, album_id=self.album.pk, expected_version=1)
        self.assertTrue(Album.objects.filter(pk=self.album.pk).exists())

    def test_other_user_cannot_update_or_delete(self):
        with self.assertRaises(Album.DoesNotExist):
            self.update(owner=self.other)
        with self.assertRaises(Album.DoesNotExist):
            delete_album(owner=self.other, album_id=self.album.pk, expected_version=1)

    def test_all_non_draft_states_are_read_only(self):
        for state in Album.State.values:
            if state == Album.State.DRAFT:
                continue
            with self.subTest(state=state):
                Album.objects.filter(pk=self.album.pk).update(state=state)
                with self.assertRaises(AlbumReadOnly):
                    self.update()
                with self.assertRaises(AlbumReadOnly):
                    delete_album(owner=self.owner, album_id=self.album.pk, expected_version=1)

    def test_expired_draft_cannot_be_revived_by_editing(self):
        Album.objects.filter(pk=self.album.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        with self.assertRaises(AlbumReadOnly):
            self.update()

    def test_owner_can_delete_draft(self):
        delete_album(owner=self.owner, album_id=self.album.pk, expected_version=1)
        self.assertFalse(Album.objects.filter(pk=self.album.pk).exists())

    def test_inactive_product_cannot_be_newly_selected(self):
        with self.assertRaises(ValidationError):
            create_album(owner=self.owner, name="No", default_print_product=self.inactive)
        with self.assertRaises(ValidationError):
            self.update(default_print_product=self.inactive)

    def test_existing_inactive_product_does_not_block_rename(self):
        PrintProduct.objects.filter(pk=self.product.pk).update(active=False)
        self.assertEqual(self.update().name, "A new name")

    def test_catalog_product_and_owner_are_protected_from_deletion(self):
        with self.assertRaises(ProtectedError):
            self.product.delete()
        with self.assertRaises(ProtectedError):
            self.owner.delete()


class AlbumConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="concurrent-owner")
        self.product = PrintProduct.objects.create(
            code="concurrent-6x4",
            name="Concurrent 6 x 4 in",
            width_mm="152.40",
            height_mm="101.60",
        )
        self.album = create_album(
            owner=self.owner,
            name="Before simultaneous edits",
            default_print_product=self.product,
        )

    def test_simultaneous_same_version_updates_return_one_conflict(self):
        barrier = Barrier(2)
        original_editable_album = services._editable_album

        def synchronised_editable_album(**kwargs):
            album = original_editable_album(**kwargs)
            barrier.wait(timeout=10)
            return album

        def edit(name):
            close_old_connections()
            try:
                return update_album(
                    owner=self.owner,
                    album_id=self.album.pk,
                    expected_version=1,
                    name=name,
                    default_print_product=self.product,
                )
            except Exception as error:
                return error
            finally:
                close_old_connections()

        with patch.object(services, "_editable_album", synchronised_editable_album):
            with ThreadPoolExecutor(max_workers=2) as executor:
                outcomes = list(executor.map(edit, ("First edit", "Second edit")))

        self.assertEqual(sum(isinstance(outcome, Album) for outcome in outcomes), 1)
        self.assertEqual(sum(isinstance(outcome, AlbumConflict) for outcome in outcomes), 1)
        self.album.refresh_from_db()
        self.assertEqual(self.album.version, 2)
        self.assertIn(self.album.name, {"First edit", "Second edit"})
