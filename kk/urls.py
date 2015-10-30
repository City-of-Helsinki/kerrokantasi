from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers

from kk.views import HearingViewSet

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'hearing', HearingViewSet)

urlpatterns = [
    url(r'^v1/', include(router.urls, namespace='v1')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('rest_framework.urls', namespace='rest_framework'))
]
