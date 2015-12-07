from nested_admin import urls as nested_admin_urls
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from democracy import urls_v1

urlpatterns = [
    url(r'^v1/', include(urls_v1)),
    url(r'^nested_admin/', include(nested_admin_urls)),
    url(r'^admin/', include(admin.site.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
