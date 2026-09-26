from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_safe

from albums.models import Album

from .forms import DeletePhotoForm, PhotoUploadForm
from .models import Photo, PhotoAsset
from .services import (
    AlbumCapacityReached,
    PhotoAlbumReadOnly,
    PhotoConflict,
    PhotoUploadRejected,
    create_photo,
    delete_photo,
)


def _json_requested(request):
    return "application/json" in request.headers.get("Accept", "")


@login_required
@require_POST
def upload_photos(request, album_id):
    get_object_or_404(Album, pk=album_id, owner=request.user)
    form = PhotoUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        error = "Choose at least one photo to upload."
        if _json_requested(request):
            return JsonResponse({"created": [], "errors": [{"message": error}]}, status=400)
        messages.error(request, error)
        return redirect("albums:detail", album_id=album_id)

    created = []
    errors = []
    for uploaded_file in form.cleaned_data["photos"]:
        try:
            photo = create_photo(
                owner=request.user,
                album_id=album_id,
                uploaded_file=uploaded_file,
                upload_id=form.cleaned_data["upload_id"],
            )
        except (PhotoUploadRejected, AlbumCapacityReached, PhotoAlbumReadOnly) as error:
            errors.append(
                {
                    "filename": Path(uploaded_file.name).name,
                    "message": str(error),
                    "code": getattr(error, "code", "unavailable"),
                }
            )
        else:
            created.append({"id": str(photo.pk), "filename": photo.original_filename})

    if _json_requested(request):
        return JsonResponse(
            {"created": created, "errors": errors},
            status=201 if created and not errors else 400,
        )
    if created:
        messages.success(
            request, f"Uploaded {len(created)} photo{'s' if len(created) != 1 else ''}."
        )
    for error in errors:
        messages.error(request, f"{error['filename']}: {error['message']}")
    return redirect("albums:detail", album_id=album_id)


@login_required
@require_safe
def asset_content(request, asset_id):
    asset = get_object_or_404(
        PhotoAsset.objects.select_related("photo__album"),
        pk=asset_id,
        photo__album__owner=request.user,
    )
    is_preview = asset.kind == PhotoAsset.Kind.PREVIEW
    filename = (
        f"{Path(asset.photo.original_filename).stem}-preview.jpg"
        if is_preview
        else asset.photo.original_filename
    )
    response = FileResponse(
        asset.file.open("rb"),
        as_attachment=not is_preview,
        filename=filename,
        content_type=asset.media_type,
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
@require_POST
def remove_photo(request, photo_id):
    photo = get_object_or_404(
        Photo.objects.select_related("album"), pk=photo_id, album__owner=request.user
    )
    album_id = photo.album_id
    form = DeletePhotoForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("A valid album version is required.")
    try:
        delete_photo(
            owner=request.user,
            photo_id=photo.pk,
            expected_album_version=form.cleaned_data["version"],
        )
    except (PhotoAlbumReadOnly, PhotoConflict) as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Photo removed.")
    return redirect("albums:detail", album_id=album_id)
