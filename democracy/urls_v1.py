from django.conf.urls import include, url
from rest_framework_nested import routers

from democracy.views import (
    HearingCommentViewSet, HearingImageViewSet, HearingViewSet, SectionCommentViewSet, SectionViewSet, UserDataViewSet
)

router = routers.DefaultRouter()
router.register(r'hearing', HearingViewSet, base_name='hearing')
router.register(r'users', UserDataViewSet, base_name='users')

hearing_comments_router = routers.NestedSimpleRouter(router, r'hearing', lookup='comment_parent')
hearing_comments_router.register(r'comments', HearingCommentViewSet, base_name='comments')

hearing_child_router = routers.NestedSimpleRouter(router, r'hearing', lookup='hearing')
hearing_child_router.register(r'sections', SectionViewSet, base_name='sections')
hearing_child_router.register(r'images', HearingImageViewSet, base_name='images')

section_comments_router = routers.NestedSimpleRouter(hearing_child_router, r'sections', lookup='comment_parent')
section_comments_router.register(r'comments', SectionCommentViewSet, base_name='comments')

urlpatterns = [
    url(r'^', include(router.urls, namespace='v1')),
    url(r'^', include(hearing_comments_router.urls, namespace='v1')),
    url(r'^', include(hearing_child_router.urls, namespace='v1')),
    url(r'^', include(section_comments_router.urls, namespace='v1')),
]
