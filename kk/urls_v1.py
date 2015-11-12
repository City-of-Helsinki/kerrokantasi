from django.conf.urls import include, url
from kk.views import HearingCommentViewSet, HearingImageViewSet, HearingViewSet, ScenarioCommentViewSet, ScenarioViewSet
from rest_framework_nested import routers

router = routers.SimpleRouter()
router.register(r'hearing', HearingViewSet)

hearing_comments_router = routers.NestedSimpleRouter(router, r'hearing', lookup='comment_parent')
hearing_comments_router.register(r'comments', HearingCommentViewSet, base_name='comments')

hearing_child_router = routers.NestedSimpleRouter(router, r'hearing', lookup='hearing')
hearing_child_router.register(r'scenarios', ScenarioViewSet, base_name='scenarios')
hearing_child_router.register(r'images', HearingImageViewSet, base_name='images')

scenario_comments_router = routers.NestedSimpleRouter(hearing_child_router, r'scenarios', lookup='comment_parent')
scenario_comments_router.register(r'comments', ScenarioCommentViewSet, base_name='comments')

urlpatterns = [
    url(r'^', include(router.urls, namespace='v1')),
    url(r'^', include(hearing_comments_router.urls, namespace='v1')),
    url(r'^', include(hearing_child_router.urls, namespace='v1')),
    url(r'^', include(scenario_comments_router.urls, namespace='v1')),
]
