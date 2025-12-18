"""
Shared OpenAPI parameter and response definitions for API documentation.

This module contains reusable OpenApiParameter objects and response serializers
that are used across multiple viewsets to keep decorator definitions clean and DRY.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, inline_serializer
from rest_framework import serializers

# ============================================================================
# Pagination Parameters
# ============================================================================

PAGINATION_PARAMS = [
    OpenApiParameter(
        "limit",
        OpenApiTypes.INT,
        description="Number of results per page",
    ),
    OpenApiParameter(
        "offset",
        OpenApiTypes.INT,
        description="Offset for pagination",
    ),
]

# ============================================================================
# Common Query Parameters
# ============================================================================

AUTHORIZATION_CODE_PARAM = [
    OpenApiParameter(
        "authorization_code",
        OpenApiTypes.STR,
        description="Authorization code for viewing comment",
        location=OpenApiParameter.QUERY,
    ),
]

ORDERING_PARAM = [
    OpenApiParameter(
        "ordering",
        OpenApiTypes.STR,
        description="Sort field (prefix - for descending order)",
    ),
]

HEARING_ORDERING_PARAM = [
    OpenApiParameter(
        "ordering",
        OpenApiTypes.STR,
        description=(
            "Sort field: created_at, close_at, open_at, n_comments (prefix - for desc)"
        ),
    ),
]

BBOX_PARAM = [
    OpenApiParameter(
        "bbox",
        OpenApiTypes.STR,
        description="Bounding box filter: min_lon,min_lat,max_lon,max_lat",
    ),
]

INCLUDE_PARAM = [
    OpenApiParameter(
        "include",
        OpenApiTypes.STR,
        description="Include additional data (e.g., 'plugin_data', 'geojson')",
    ),
]

# ============================================================================
# Comment-Related Parameters
# ============================================================================

COMMENT_ORDERING_PARAM = [
    OpenApiParameter(
        "ordering",
        OpenApiTypes.STR,
        description="Sort field: created_at, n_votes (prefix - for desc)",
    ),
]

COMMENT_FILTER_PARAMS = [
    OpenApiParameter(
        "authorization_code",
        OpenApiTypes.STR,
        description="Authorization code for viewing specific comments",
    ),
]

COMMON_COMMENT_PARAMS = (
    COMMENT_FILTER_PARAMS + COMMENT_ORDERING_PARAM + BBOX_PARAM + INCLUDE_PARAM
)

# ============================================================================
# Root-Level Comment Filter Parameters
# ============================================================================

ROOT_COMMENT_FILTER_PARAMS = [
    OpenApiParameter(
        "hearing",
        OpenApiTypes.STR,
        description="Filter by hearing ID",
    ),
    OpenApiParameter(
        "section",
        OpenApiTypes.STR,
        description="Filter by section ID",
    ),
    OpenApiParameter(
        "comment",
        OpenApiTypes.STR,
        description="Filter by parent comment ID",
    ),
    OpenApiParameter(
        "label",
        OpenApiTypes.STR,
        description="Filter by label ID",
    ),
    OpenApiParameter(
        "pinned",
        OpenApiTypes.BOOL,
        description="Filter for pinned comments",
    ),
    OpenApiParameter(
        "created_by",
        OpenApiTypes.STR,
        description="Filter by creator ('me' for current user)",
    ),
    OpenApiParameter(
        "created_at__lt",
        OpenApiTypes.DATETIME,
        description="Filter comments created before this date",
    ),
    OpenApiParameter(
        "created_at__gt",
        OpenApiTypes.DATETIME,
        description="Filter comments created after this date",
    ),
]

# ============================================================================
# Hearing Filter Parameters
# ============================================================================

HEARING_FILTER_PARAMS = [
    OpenApiParameter(
        "title",
        OpenApiTypes.STR,
        description="Filter by title (case-insensitive contains)",
    ),
    OpenApiParameter(
        "open_at_lte",
        OpenApiTypes.DATETIME,
        description="Filter hearings opening at or before this date",
    ),
    OpenApiParameter(
        "open_at_gt",
        OpenApiTypes.DATETIME,
        description="Filter hearings opening after this date",
    ),
    OpenApiParameter(
        "label",
        OpenApiTypes.STR,
        description="Filter by label ID (comma-separated for multiple)",
    ),
    OpenApiParameter(
        "published",
        OpenApiTypes.BOOL,
        description="Filter by published status",
    ),
    OpenApiParameter(
        "open",
        OpenApiTypes.BOOL,
        description="Filter by open/closed status",
    ),
    OpenApiParameter(
        "following",
        OpenApiTypes.BOOL,
        description="Filter hearings followed by current user",
    ),
    OpenApiParameter(
        "created_by",
        OpenApiTypes.STR,
        description="Filter by creator ('me' for current user or organization name)",
    ),
]

# ============================================================================
# Section Filter Parameters
# ============================================================================

SECTION_FILTER_PARAMS = [
    OpenApiParameter(
        "hearing",
        OpenApiTypes.STR,
        description="Filter by hearing ID",
    ),
    OpenApiParameter(
        "type",
        OpenApiTypes.STR,
        description="Filter by section type identifier",
    ),
]

SECTION_IMAGE_FILTER_PARAMS = [
    OpenApiParameter(
        "hearing",
        OpenApiTypes.STR,
        description="Filter by hearing ID",
    ),
    OpenApiParameter(
        "section",
        OpenApiTypes.STR,
        description="Filter by section ID",
    ),
]

# ============================================================================
# Label Filter Parameters
# ============================================================================

LABEL_FILTER_PARAMS = [
    OpenApiParameter(
        "label",
        OpenApiTypes.STR,
        description="Filter by label text (case-insensitive contains)",
    ),
]

# ============================================================================
# Common Response Serializers
# ============================================================================

# Generic status response used across all endpoints
# Returns: {"status": "string message"}
# This consolidated response is used for all actions that return a simple
# status message, including voting, flagging, following, and deletion operations.
RESPONSE_WITH_STATUS = inline_serializer(
    name="StatusResponse",
    fields={"status": serializers.CharField()},
)
