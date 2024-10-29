from django.urls import include, path, re_path
from rest_framework_nested import routers

from democracy.views import (
    CommentViewSet,
    ContactPersonViewSet,
    FileViewSet,
    HearingViewSet,
    ImageViewSet,
    LabelViewSet,
    OrganizationViewSet,
    ProjectViewSet,
    RootSectionViewSet,
    SectionCommentViewSet,
    SectionViewSet,
    ServeFileView,
    UserDataViewSet,
)

router = routers.DefaultRouter()
router.register(r"hearing", HearingViewSet, basename="hearing")
router.register(r"users", UserDataViewSet, basename="users")
router.register(r"comment", CommentViewSet, basename="comment")
router.register(r"image", ImageViewSet, basename="image")
router.register(r"section", RootSectionViewSet, basename="section")
router.register(r"label", LabelViewSet, basename="label")
router.register(r"contact_person", ContactPersonViewSet, basename="contact_person")
router.register(r"project", ProjectViewSet, basename="project")
router.register(r"file", FileViewSet, basename="file")
router.register(r"organization", OrganizationViewSet, basename="organization")

hearing_child_router = routers.NestedSimpleRouter(router, r"hearing", lookup="hearing")
hearing_child_router.register(r"sections", SectionViewSet, basename="sections")

section_comments_router = routers.NestedSimpleRouter(
    hearing_child_router, r"sections", lookup="comment_parent"
)
section_comments_router.register(
    r"comments", SectionCommentViewSet, basename="comments"
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(hearing_child_router.urls)),
    path("", include(section_comments_router.urls)),
    re_path(
        r"^download/(?P<filetype>sectionfile|sectionimage)/(?P<pk>\d+)/$",
        ServeFileView.as_view(),
        name="serve_file",
    ),
]
