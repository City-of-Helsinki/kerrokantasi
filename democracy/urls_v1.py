from django.conf.urls import include, url
from rest_framework_nested import routers

from democracy.views import (
    CommentViewSet, ContactPersonViewSet, HearingViewSet, ImageViewSet, LabelViewSet, ProjectViewSet,
    RootSectionViewSet, SectionCommentViewSet, SectionViewSet, UserDataViewSet, FileViewSet, ServeFileView
)

router = routers.DefaultRouter()
router.register(r'hearing', HearingViewSet, base_name='hearing')
router.register(r'users', UserDataViewSet, base_name='users')
router.register(r'comment', CommentViewSet, base_name='comment')
router.register(r'image', ImageViewSet, base_name='image')
router.register(r'section', RootSectionViewSet, base_name='section')
router.register(r'label', LabelViewSet, base_name='label')
router.register(r'contact_person', ContactPersonViewSet, base_name='contact_person')
router.register(r'project', ProjectViewSet, base_name='project')
router.register(r'file', FileViewSet, base_name='file')

hearing_child_router = routers.NestedSimpleRouter(router, r'hearing', lookup='hearing')
hearing_child_router.register(r'sections', SectionViewSet, base_name='sections')

section_comments_router = routers.NestedSimpleRouter(hearing_child_router, r'sections', lookup='comment_parent')
section_comments_router.register(r'comments', SectionCommentViewSet, base_name='comments')

urlpatterns = [
    url(r'^', include(router.urls, namespace='v1')),
    url(r'^', include(hearing_child_router.urls, namespace='v1')),
    url(r'^', include(section_comments_router.urls, namespace='v1')),
    url(r'^download/(?P<filetype>sectionfile|sectionimage)/(?P<pk>\d+)/$', ServeFileView.as_view(), name='serve_file'),
]
