from django.conf.urls import include, url
from rest_framework_nested import routers

from democracy.views import (
    CommentViewSet, ContactPersonViewSet, HearingViewSet, ImageViewSet, LabelViewSet, RootSectionViewSet,
    SectionCommentViewSet, SectionViewSet, UserDataViewSet
)

router = routers.DefaultRouter()
router.register(r'hearing', HearingViewSet, base_name='hearing')
router.register(r'users', UserDataViewSet, base_name='users')
router.register(r'comment', CommentViewSet, base_name='comment')
router.register(r'image', ImageViewSet, base_name='image')
router.register(r'section', RootSectionViewSet, base_name='section')
router.register(r'label', LabelViewSet, base_name='label')
router.register(r'contact_person', ContactPersonViewSet, base_name='contact_person')

hearing_comments_router = routers.NestedSimpleRouter(router, r'hearing', lookup='comment_parent')

hearing_child_router = routers.NestedSimpleRouter(router, r'hearing', lookup='hearing')
hearing_child_router.register(r'sections', SectionViewSet, base_name='sections')

section_comments_router = routers.NestedSimpleRouter(hearing_child_router, r'sections', lookup='comment_parent')
section_comments_router.register(r'comments', SectionCommentViewSet, base_name='comments')

urlpatterns = [
    url(r'^', include(router.urls, namespace='v1')),
    url(r'^', include(hearing_comments_router.urls, namespace='v1')),
    url(r'^', include(hearing_child_router.urls, namespace='v1')),
    url(r'^', include(section_comments_router.urls, namespace='v1')),
]
