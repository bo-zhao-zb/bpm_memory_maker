from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from .forms import AlbumForm, DeleteAlbumForm
from .models import Album
from .services import AlbumConflict, AlbumReadOnly, create_album, delete_album, update_album


def _owned_album(request, album_id):
    return get_object_or_404(
        Album.objects.select_related("default_print_product"), pk=album_id, owner=request.user
    )


@login_required
@require_safe
def album_list(request):
    albums = Album.objects.filter(owner=request.user).select_related("default_print_product")
    page = Paginator(albums, 24).get_page(request.GET.get("page"))
    return render(request, "albums/list.html", {"page_obj": page})


@login_required
@require_safe
def album_detail(request, album_id):
    return render(request, "albums/detail.html", {"album": _owned_album(request, album_id)})


@login_required
@require_http_methods(["GET", "POST"])
def album_create(request):
    form = AlbumForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            album = create_album(owner=request.user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Album created.")
            return redirect(album)
    return render(request, "albums/form.html", {"form": form}, status=400 if form.is_bound else 200)


@login_required
@require_http_methods(["GET", "POST"])
def album_edit(request, album_id):
    album = _owned_album(request, album_id)
    if not album.is_editable:
        return render(request, "albums/locked.html", {"album": album}, status=409)
    form = AlbumForm(request.POST if request.method == "POST" else None, album=album)
    status = 400 if form.is_bound else 200
    conflict = False
    if request.method == "POST" and form.is_valid():
        try:
            updated = update_album(
                owner=request.user,
                album_id=album.pk,
                expected_version=form.cleaned_data["version"],
                name=form.cleaned_data["name"],
                default_print_product=form.cleaned_data["default_print_product"],
            )
        except Album.DoesNotExist as error:
            raise Http404 from error
        except (AlbumConflict, AlbumReadOnly) as error:
            form.add_error(None, str(error))
            status, conflict = 409, True
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Album updated.")
            return redirect(updated)
    return render(
        request,
        "albums/form.html",
        {"form": form, "album": album, "conflict": conflict},
        status=status,
    )


@login_required
@require_http_methods(["GET", "POST"])
def album_delete(request, album_id):
    album = _owned_album(request, album_id)
    if not album.is_editable:
        return render(request, "albums/locked.html", {"album": album}, status=409)
    form = DeleteAlbumForm(
        request.POST if request.method == "POST" else None, initial={"version": album.version}
    )
    status = 400 if form.is_bound else 200
    if request.method == "POST" and form.is_valid():
        try:
            delete_album(
                owner=request.user, album_id=album.pk, expected_version=form.cleaned_data["version"]
            )
        except Album.DoesNotExist as error:
            raise Http404 from error
        except (AlbumConflict, AlbumReadOnly) as error:
            form.add_error(None, str(error))
            status = 409
        else:
            messages.success(request, "Album deleted.")
            return redirect("albums:list")
    return render(request, "albums/delete.html", {"form": form, "album": album}, status=status)
