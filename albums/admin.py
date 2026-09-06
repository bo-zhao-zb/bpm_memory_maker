from django.contrib import admin

from .models import Album


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "state", "default_print_product", "expires_at")
    list_filter = ("state",)
    search_fields = ("name", "owner__username")
    list_select_related = ("owner", "default_print_product")
    readonly_fields = (
        "id",
        "owner",
        "name",
        "state",
        "default_print_product",
        "photo_limit",
        "expires_at",
        "version",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
