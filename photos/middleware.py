from django.conf import settings
from django.http import HttpResponse


class PhotoUploadSizeLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path.endswith("/photos/upload/"):
            try:
                content_length = int(request.headers.get("Content-Length", "0"))
            except ValueError:
                content_length = 0
            if content_length > settings.PHOTO_MAX_REQUEST_SIZE:
                return HttpResponse("Upload request is too large.", status=413)
        return self.get_response(request)
