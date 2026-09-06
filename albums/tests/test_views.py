from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from albums.models import Album
from albums.services import create_album, update_album
from catalog.models import PrintProduct


class AlbumViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="owner")
        cls.other = get_user_model().objects.create_user(username="other")
        cls.product = PrintProduct.objects.create(
            code="6x4", name="6 x 4 in", width_mm="152.40", height_mm="101.60"
        )

    def setUp(self):
        self.client.force_login(self.owner)
        self.album = create_album(
            owner=self.owner, name="Private summer", default_print_product=self.product
        )

    def url(self, action):
        return reverse(f"albums:{action}", args=[self.album.pk])

    def test_full_album_journey(self):
        response = self.client.post(
            reverse("albums:create"),
            {"name": "Weekend", "default_print_product": self.product.pk, "owner": self.other.pk},
        )
        created = Album.objects.get(name="Weekend")
        self.assertEqual(created.owner, self.owner)
        self.assertRedirects(response, created.get_absolute_url())
        response = self.client.post(
            reverse("albums:edit", args=[created.pk]),
            {"name": "Long weekend", "default_print_product": self.product.pk, "version": 1},
        )
        self.assertRedirects(response, created.get_absolute_url())
        self.assertContains(self.client.get(reverse("albums:list")), "Long weekend")
        response = self.client.post(reverse("albums:delete", args=[created.pk]), {"version": 2})
        self.assertRedirects(response, reverse("albums:list"))
        self.assertFalse(Album.objects.filter(pk=created.pk).exists())

    def test_login_required_for_every_album_route(self):
        self.client.logout()
        for url in [
            reverse("albums:list"),
            reverse("albums:create"),
            *(self.url(action) for action in ("detail", "edit", "delete")),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)
                self.assertEqual(self.client.post(url).status_code, 302)

    def test_other_user_cannot_list_read_edit_or_delete(self):
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse("albums:list")), self.album.name)
        for action in ("detail", "edit", "delete"):
            with self.subTest(action=action):
                self.assertEqual(self.client.get(self.url(action)).status_code, 404)
                response = self.client.post(self.url(action), {"name": "Taken", "version": 1})
                self.assertEqual(response.status_code, 404 if action != "detail" else 405)

    def test_invalid_create_is_not_persisted(self):
        response = self.client.post(
            reverse("albums:create"), {"name": " ", "default_print_product": self.product.pk}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Album.objects.count(), 1)

    def test_delete_get_only_confirms(self):
        self.assertContains(self.client.get(self.url("delete")), "Delete this album?")
        self.assertTrue(Album.objects.filter(pk=self.album.pk).exists())

    def test_missing_delete_version_is_rejected(self):
        self.assertEqual(self.client.post(self.url("delete")).status_code, 400)
        self.assertTrue(Album.objects.filter(pk=self.album.pk).exists())

    def test_stale_edit_and_delete_offer_recovery(self):
        update_album(
            owner=self.owner,
            album_id=self.album.pk,
            expected_version=1,
            name="Newer",
            default_print_product=self.product,
        )
        response = self.client.post(
            self.url("edit"),
            {"name": "Older", "default_print_product": self.product.pk, "version": 1},
        )
        self.assertContains(response, "Reload album", status_code=409)
        response = self.client.post(self.url("delete"), {"version": 1})
        self.assertContains(response, "Reload album", status_code=409)
        self.album.refresh_from_db()
        self.assertEqual(self.album.name, "Newer")

    def test_non_draft_mutations_are_rejected(self):
        Album.objects.filter(pk=self.album.pk).update(state=Album.State.SUBMITTED)
        self.assertNotContains(self.client.get(self.url("detail")), "Edit album")
        self.assertEqual(
            self.client.post(self.url("edit"), {"name": "No", "version": 1}).status_code, 409
        )
        self.assertEqual(self.client.post(self.url("delete"), {"version": 1}).status_code, 409)

    def test_csrf_is_required_for_mutations(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for url in (
            reverse("albums:create"),
            self.url("edit"),
            self.url("delete"),
            reverse("account_logout"),
        ):
            with self.subTest(url=url):
                self.assertEqual(client.post(url, {"version": 1}).status_code, 403)

    def test_list_paginates_and_invalid_page_is_safe(self):
        Album.objects.bulk_create(
            [
                Album(owner=self.owner, name=f"Album {number}", default_print_product=self.product)
                for number in range(25)
            ]
        )
        response = self.client.get(reverse("albums:list"))
        self.assertEqual(len(response.context["page_obj"]), 24)
        self.assertEqual(
            self.client.get(reverse("albums:list"), {"page": "invalid"}).status_code, 200
        )

    def test_album_names_are_html_escaped(self):
        Album.objects.filter(pk=self.album.pk).update(name='<script>alert("unsafe")</script>')
        response = self.client.get(self.url("detail"))
        self.assertNotContains(response, '<script>alert("unsafe")</script>')
        self.assertContains(response, "&lt;script&gt;")
