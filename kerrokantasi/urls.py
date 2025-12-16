import helsinki_notification.contrib.rest_framework.urls
from django.conf import settings
from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe
from django.views.generic.base import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from helusers.admin_site import admin
from nested_admin import urls as nested_admin_urls

from democracy import urls_v1


#
# Kubernetes liveness & readiness probes
#
@require_safe
@never_cache
def healthz(*_, **__):
    return HttpResponse(status=200)


@require_safe
@never_cache
def readiness(*_, **__):
    return HttpResponse(status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("helusers.urls")),
    path("", include("social_django.urls", namespace="social")),
    path("v1/", include(urls_v1)),
    path("v1/", include(helsinki_notification.contrib.rest_framework.urls)),
    path("nested_admin/", include(nested_admin_urls)),
    path("gdpr-api/", include("helsinki_gdpr.urls")),
    path("api-docs/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path(
        "api-docs/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api-docs/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("healthz", healthz, name="healthz"),
    path("readiness", readiness, name="readiness"),
    path("", RedirectView.as_view(url="v1/")),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG_TOOLBAR:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
