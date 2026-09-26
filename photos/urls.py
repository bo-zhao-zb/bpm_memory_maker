from django.urls import path

from . import views

app_name = "photos"
urlpatterns = [
    path("albums/<uuid:album_id>/photos/upload/", views.upload_photos, name="upload"),
    path("photos/<uuid:photo_id>/delete/", views.remove_photo, name="delete"),
    path("photos/assets/<uuid:asset_id>/", views.asset_content, name="asset"),
]
