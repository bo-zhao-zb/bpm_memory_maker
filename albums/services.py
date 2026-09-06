from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from catalog.models import PrintProduct

from .models import Album, draft_expiry


class AlbumConflict(Exception):
    pass


class AlbumReadOnly(Exception):
    pass


def _require_owner(owner):
    if not owner.is_authenticated or not owner.is_active:
        raise PermissionDenied


def _editable_album(*, owner, album_id, expected_version):
    _require_owner(owner)
    album = Album.objects.get(pk=album_id, owner=owner)
    if not album.is_editable:
        raise AlbumReadOnly("This album is no longer an editable draft.")
    if album.version != expected_version:
        raise AlbumConflict("This album changed in another session. Reload it before trying again.")
    return album


def _validate_product(product, current_product_id=None):
    if product.pk == current_product_id:
        return
    if not PrintProduct.objects.filter(pk=product.pk, active=True).exists():
        raise ValidationError({"default_print_product": "Choose an available print size."})


def create_album(*, owner, name, default_print_product):
    _require_owner(owner)
    _validate_product(default_print_product)
    album = Album(owner=owner, name=name, default_print_product=default_print_product)
    album.full_clean()
    album.save()
    return album


@transaction.atomic
def update_album(*, owner, album_id, expected_version, name, default_print_product):
    album = _editable_album(owner=owner, album_id=album_id, expected_version=expected_version)
    _validate_product(default_print_product, album.default_print_product_id)
    album.name = name
    album.default_print_product = default_print_product
    album.full_clean()
    updated = Album.objects.filter(
        pk=album.pk,
        owner=owner,
        state=Album.State.DRAFT,
        version=expected_version,
        expires_at__gt=timezone.now(),
    ).update(
        name=album.name,
        default_print_product=default_print_product,
        version=F("version") + 1,
        updated_at=timezone.now(),
        expires_at=draft_expiry(),
    )
    if not updated:
        raise AlbumConflict("This album changed in another session. Reload it before trying again.")
    album.refresh_from_db()
    return album


@transaction.atomic
def delete_album(*, owner, album_id, expected_version):
    album = _editable_album(owner=owner, album_id=album_id, expected_version=expected_version)
    claimed = Album.objects.filter(
        pk=album.pk,
        owner=owner,
        state=Album.State.DRAFT,
        version=expected_version,
        expires_at__gt=timezone.now(),
    ).update(version=F("version") + 1)
    if not claimed:
        raise AlbumConflict("This album changed in another session. Reload it before trying again.")
    album.delete()
