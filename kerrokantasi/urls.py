from django.conf import settings
from django.urls import include, path
from django.views.generic.base import RedirectView
from helusers.admin_site import admin
from nested_admin import urls as nested_admin_urls

from democracy import urls_v1

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("helusers.urls")),
    path("", include("social_django.urls", namespace="social")),
    path("v1/", include(urls_v1)),
    path("nested_admin/", include(nested_admin_urls)),
    path("gdpr-api/", include("helsinki_gdpr.urls")),
    path("", RedirectView.as_view(url="v1/")),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG_TOOLBAR:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
