from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve


def health_check(request):
    return JsonResponse({"status": "ok", "app": "CholoGhuri Smart Bangladesh Tourism Platform"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="api-health"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("tourism.urls")),
    path("", include("tourism.web_urls")),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT if settings.STATIC_ROOT.exists() else settings.STATICFILES_DIRS[0]}),
]
