from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import include, path
from django.views.decorators.cache import never_cache
from django.views.generic.base import RedirectView
from helusers.admin_site import admin
from nested_admin import urls as nested_admin_urls

from democracy import urls_v1
from democracy.views.upload import browse, upload

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("helusers.urls")),
    path("", include("social_django.urls", namespace="social")),
    path("v1/", include(urls_v1)),
    path("nested_admin/", include(nested_admin_urls)),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("upload/", staff_member_required(upload), name="ckeditor_upload"),
    path("browse/", never_cache(staff_member_required(browse)), name="ckeditor_browse"),
    path("", RedirectView.as_view(url="v1/")),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG_TOOLBAR:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
