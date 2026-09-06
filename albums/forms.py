from django import forms
from django.db.models import Q

from catalog.models import PrintProduct


class AlbumForm(forms.Form):
    name = forms.CharField(
        label="Album name", max_length=100, widget=forms.TextInput(attrs={"autocomplete": "off"})
    )
    default_print_product = forms.ModelChoiceField(
        label="Default print size",
        queryset=PrintProduct.objects.none(),
        empty_label="Choose a size",
    )
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)

    def __init__(self, *args, album=None, **kwargs):
        super().__init__(*args, **kwargs)
        available = Q(active=True)
        if album:
            available |= Q(pk=album.default_print_product_id)
            self.initial.update(
                name=album.name,
                default_print_product=album.default_print_product_id,
                version=album.version,
            )
        else:
            self.fields.pop("version")
        self.fields["default_print_product"].queryset = PrintProduct.objects.filter(available)


class DeleteAlbumForm(forms.Form):
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
