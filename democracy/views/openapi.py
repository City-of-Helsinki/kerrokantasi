"""
Shared OpenAPI parameter and response definitions for API documentation.

This module contains reusable OpenApiParameter objects and response serializers
that are used across multiple viewsets to keep decorator definitions clean and DRY.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, inline_serializer
from rest_framework import serializers

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
