from django import forms
from django.conf import settings


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, list | tuple):
            files = [single_clean(item, initial) for item in data]
            if len(files) > settings.PHOTO_MAX_FILES_PER_REQUEST:
                raise forms.ValidationError(
                    f"Choose no more than {settings.PHOTO_MAX_FILES_PER_REQUEST} files at once.",
                    code="too_many_files",
                )
            return files
        return [single_clean(data, initial)]


class PhotoUploadForm(forms.Form):
    upload_id = forms.UUIDField(required=False)
    photos = MultipleFileField(
        widget=MultipleFileInput(
            attrs={"accept": "image/jpeg,image/png,image/heic,image/heif,.heic,.heif"}
        )
    )


class DeletePhotoForm(forms.Form):
    version = forms.IntegerField(min_value=1)
