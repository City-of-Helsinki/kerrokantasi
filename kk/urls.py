from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_nested import routers

from kk.views import HearingViewSet, ScenarioViewSet, ScenarioCommentViewSet, HearingCommentViewSet

router = routers.SimpleRouter()
router.register(r'hearing', HearingViewSet)

hearing_comments_router = routers.NestedSimpleRouter(router, r'hearing', lookup='comment_parent')
hearing_comments_router.register(r'comments', HearingCommentViewSet, base_name='comments')

scenario_router = routers.NestedSimpleRouter(router, r'hearing')
scenario_router.register(r'scenarios', ScenarioViewSet, base_name='scenarios')

scenario_comments_router = routers.NestedSimpleRouter(scenario_router, r'scenarios', lookup='comment_parent')
scenario_comments_router.register(r'comments', ScenarioCommentViewSet, base_name='comments')

urlpatterns = [
    url(r'^v1/', include(router.urls, namespace='v1')),
    url(r'^v1/', include(hearing_comments_router.urls, namespace='v1')),
    url(r'^v1/', include(scenario_router.urls, namespace='v1')),
    url(r'^v1/', include(scenario_comments_router.urls, namespace='v1')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/v1', include('rest_framework.urls', namespace='rest_framework'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
