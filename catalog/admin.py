from django.contrib import admin

from .models import PrintProduct


@admin.register(PrintProduct)
class PrintProductAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "width_mm", "height_mm", "active", "display_order")
    list_filter = ("active",)
    search_fields = ("name", "code")
