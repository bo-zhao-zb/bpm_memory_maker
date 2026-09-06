from django.urls import path

from . import views

app_name = "albums"
urlpatterns = [
    path("", views.album_list, name="list"),
    path("albums/new/", views.album_create, name="create"),
    path("albums/<uuid:album_id>/", views.album_detail, name="detail"),
    path("albums/<uuid:album_id>/edit/", views.album_edit, name="edit"),
    path("albums/<uuid:album_id>/delete/", views.album_delete, name="delete"),
]
