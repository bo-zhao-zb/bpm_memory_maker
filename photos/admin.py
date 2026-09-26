from django.contrib import admin

from .models import Photo, PhotoAsset, StoredFileDeletion


class PhotoAssetInline(admin.TabularInline):
    model = PhotoAsset
    extra = 0
    can_delete = False
    readonly_fields = (
        "id",
        "kind",
        "file",
        "checksum",
        "media_type",
        "width",
        "height",
        "byte_size",
        "created_at",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("original_filename", "album", "state", "width", "height", "created_at")
    list_filter = ("state",)
    search_fields = ("original_filename", "album__name", "album__owner__username")
    list_select_related = ("album", "album__owner")
    readonly_fields = (
        "id",
        "album",
        "display_order",
        "original_filename",
        "state",
        "width",
        "height",
        "created_at",
        "updated_at",
    )
    inlines = (PhotoAssetInline,)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StoredFileDeletion)
class StoredFileDeletionAdmin(admin.ModelAdmin):
    list_display = ("storage_key", "state", "attempt_count", "updated_at")
    list_filter = ("state",)
    search_fields = ("storage_key",)
    readonly_fields = (
        "id",
        "storage_key",
        "state",
        "attempt_count",
        "last_error",
        "created_at",
        "updated_at",
        "completed_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
