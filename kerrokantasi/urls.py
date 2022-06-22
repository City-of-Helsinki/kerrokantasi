from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path
from django.views.decorators.cache import never_cache
from django.views.generic.base import RedirectView
from helusers.admin_site import admin
from nested_admin import urls as nested_admin_urls

from democracy import urls_v1
from democracy.views.upload import browse, upload

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'', include('helusers.urls')),
    url('', include('social_django.urls', namespace='social')),
    url(r'^v1/', include(urls_v1)),
    url(r'^nested_admin/', include(nested_admin_urls)),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^upload/', staff_member_required(upload), name='ckeditor_upload'),
    url(r'^browse/', never_cache(staff_member_required(browse)), name='ckeditor_browse'),
    path('', RedirectView.as_view(url='v1/'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
