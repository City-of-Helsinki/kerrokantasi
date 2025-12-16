# Add Django REST Framework OpenAPI Documentation

Complete setup and documentation of all API endpoints using drf-spectacular with Redoc and Swagger UI.

## Execution Steps

### 1. Install Dependencies

Add to `requirements.in`:
```txt
drf-spectacular
```

Then install:
```bash
.venv/bin/pip install drf-spectacular
```

### 2. Configure Settings

In `settings.py` or `settings/base.py`:

**Add to INSTALLED_APPS:**
```python
INSTALLED_APPS = [
    # ... existing apps
    "drf_spectacular",
    # ... your apps
]
```

**Add REST_FRAMEWORK config (REQUIRED):**
```python
REST_FRAMEWORK = {
    # ... existing settings
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [  # REQUIRED to prevent AttributeError
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}
```

**Add SPECTACULAR_SETTINGS:**
```python
SPECTACULAR_SETTINGS = {
    "TITLE": "Your API Name",
    "DESCRIPTION": "API description with authentication details",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_PATCH": True,
    "SCHEMA_PATH_PREFIX": r"/v1/",  # Adjust to match your API version pattern
    "SCHEMA_PATH_PREFIX_TRIM": True,
}
```

### 3. Add or update URL Routes

NOTE: The api docs url patterns must be set as in the example below. Update them if they don't match.

In main `urls.py`:
```python
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # ... existing patterns
    path(
        "api-docs/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path(
        "api-docs/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api-docs/schema/", SpectacularAPIView.as_view(), name="schema"),
    # ... your API routes
]
```

IMPORTANT: The api docs url patterns MUST BE SET AS IN THE EXAMPLE ABOVE. UPDATE THEM IF THEY DON'T MATCH.

### 4. Fix Compatibility Issues

Search for unsafe `request.accepted_renderer` usage:
```bash
grep -r "request\.accepted_renderer" --include="*.py" .
```

Replace pattern:
```python
# Bad - fails during schema generation
if isinstance(request.accepted_renderer, SomeRenderer):
    ...

# Good - safe for schema generation
accepted_renderer = getattr(request, "accepted_renderer", None)
if isinstance(accepted_renderer, SomeRenderer):
    ...
```

### 5. Discover All Endpoints

Find all view files containing:
- `viewsets.ModelViewSet` or `viewsets.ViewSet`
- `APIView` classes
- `@api_view` decorated functions
- `@action` decorated methods

Create inventory of:
- HTTP methods
- URL patterns
- View/action names
- File locations

### 6. Document Using Native DRF Features First

**Priority: Use native type hints and DRF/Django features that drf-spectacular automatically infers**

drf-spectacular automatically documents:

1. **Model field `help_text`** (inherited by serializers):
   ```python
   class Hearing(models.Model):
       title = models.CharField(
           max_length=255, help_text="Hearing title"
       )
       close_at = models.DateTimeField(
           help_text="When hearing closes for comments"
       )
   ```

2. **Serializer field `help_text`**:
   ```python
   class SectionSerializer(serializers.ModelSerializer):
       n_comments = serializers.SerializerMethodField(
           help_text="Total comments on section"
       )
       images = SectionImageSerializer(
           many=True, read_only=True, help_text="Attached images"
       )
   ```

3. **FilterSet field `help_text`**:
   ```python
   class HearingFilterSet(django_filters.rest_framework.FilterSet):
       title = django_filters.CharFilter(
           lookup_expr="icontains",
           help_text="Filter by title (case-insensitive)",
       )
   ```

4. **Python docstrings** (ViewSets, actions, functions):
   ```python
   class HearingViewSet(viewsets.ModelViewSet):
       """Manage participatory democracy hearings."""

       def list(self, request, *args, **kwargs):
           """List all hearings with filtering and pagination."""
   ```

5. **Type hints**:
   ```python
   def custom_action(
       self, request: Request, pk: Optional[int] = None
   ) -> Response:
       """Custom action with type-hinted parameters."""
   ```

6. **Field constraints** (max_length, required, choices, validators, min_value, max_value)

7. **Enum docstrings**:
   ```python
   class Commenting(Enum):
       """Commenting modes: NONE, REGISTERED, OPEN, STRONG."""

       NONE = "none"
   ```

**Implementation Priority:**
1. Add `help_text` to FilterSets (immediate API usability)
2. Add `help_text` to model fields (base documentation)
3. Add `help_text` to serializer fields
4. Add ViewSet/action docstrings (if not already documented. Keep them concise and to the point.)
5. Add Enum docstrings (if not already documented. Keep them concise and to the point.)

**Only use `@extend_schema` for:**
- Complex request/response schemas not in serializers
- Custom error responses
- Side effects not obvious from code
- Operations not following standard CRUD patterns

### 7. Organize OpenAPI Parameters and Response Serializers (REQUIRED)

**IMPORTANT:** Before adding any `@extend_schema` decorators, organize parameters and response serializers properly:

1. **Common parameters** go in `/democracy/views/openapi.py`
2. **Common response serializers** go in `/democracy/views/openapi.py`
3. **View-specific parameters** stay in the view file where they're used
4. **NEVER use inline_serializer in decorators** - extract them to `openapi.py`

**Structure of `openapi.py`:**
```python
"""Shared OpenAPI parameter and response definitions for API documentation.

This module contains reusable OpenApiParameter objects and response serializers
that are used across multiple viewsets to keep decorator definitions clean and
DRY.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, inline_serializer
from rest_framework import serializers

# ==========================================================================
# Pagination Parameters
# ==========================================================================

PAGINATION_PARAMS = [
    OpenApiParameter(
        "limit",
        OpenApiTypes.INT,
        description="Number of results per page",
    ),
    OpenApiParameter(
        "offset", OpenApiTypes.INT, description="Offset for pagination"
    ),
]

# ==========================================================================
# Common Query Parameters
# ==========================================================================

AUTHORIZATION_CODE_PARAM = [
    OpenApiParameter(
        "authorization_code",
        OpenApiTypes.STR,
        description="Authorization code for viewing comment",
        location=OpenApiParameter.QUERY,
    ),
]

# Add more common parameter groups as needed...

# ==========================================================================
# Common Response Serializers
# ==========================================================================

# Generic status response used across all endpoints
# Returns: {"status": "string message"}
# This consolidated response is used for all actions that return a simple
# status message, including voting, flagging, following, and deletion
# operations.
RESPONSE_WITH_STATUS = inline_serializer(
    name="StatusResponse",
    fields={"status": serializers.CharField()},
)

# Add more common response serializers as needed...
```

**Critical Rule: Consolidate Identical Response Structures**

When multiple endpoints return the same response structure, **consolidate them into a single reusable constant**:

```python
# ❌ BAD - Multiple serializers with identical structure (violates DRY)
VOTE_COUNTED_RESPONSE = inline_serializer(
    name="VoteCountedResponse",
    fields={"status": serializers.CharField()},
)
VOTE_ADDED_RESPONSE = inline_serializer(
    name="VoteAddedResponse",
    fields={"status": serializers.CharField()},
)
COMMENT_FLAGGED_RESPONSE = inline_serializer(
    name="CommentFlaggedResponse",
    fields={"status": serializers.CharField()},
)

# ✅ GOOD - Single consolidated serializer
RESPONSE_WITH_STATUS = inline_serializer(
    name="StatusResponse",
    fields={"status": serializers.CharField()},
)
```

**In view files:**
```python
from democracy.views.openapi import (
    COMMON_FILTER_PARAMS,
    PAGINATION_PARAMS,
    RESPONSE_WITH_STATUS,  # Import common response serializers
)

# View-specific parameters (keep these in the view file)
VIEW_SPECIFIC_PARAMS = [
    OpenApiParameter(
        "custom_param",
        OpenApiTypes.STR,
        description="View-specific parameter",
    ),
]


@extend_schema_view(
    list=extend_schema(
        summary="List all items",
        parameters=PAGINATION_PARAMS
        + COMMON_FILTER_PARAMS
        + VIEW_SPECIFIC_PARAMS,
    ),
    retrieve=extend_schema(summary="Get item by ID"),
    destroy=extend_schema(
        summary="Delete item",
        responses={
            200: RESPONSE_WITH_STATUS,  # Use consolidated response
            403: OpenApiResponse(description="Permission denied"),
        },
    ),
)
class YourViewSet(viewsets.ModelViewSet):
    """Brief description of what this ViewSet manages."""

    queryset = YourModel.objects.all()
    serializer_class = YourSerializer
```

### 8. Add Explicit @extend_schema Documentation

**For ViewSets:**
```python
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import serializers

from democracy.views.openapi import PAGINATION_PARAMS


@extend_schema_view(
    list=extend_schema(
        summary="List all items",
        parameters=PAGINATION_PARAMS
        + [
            OpenApiParameter(
                "status",
                OpenApiTypes.STR,
                description="Filter by status",
                enum=["active", "inactive"],
            ),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                description="Sort field (prefix - for desc)",
            ),
        ],
    ),
    retrieve=extend_schema(summary="Get item by ID"),
    create=extend_schema(
        summary="Create new item",
        responses={
            201: YourSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
    ),
    update=extend_schema(summary="Update item"),
    partial_update=extend_schema(summary="Partially update item"),
    destroy=extend_schema(summary="Delete item"),
)
class YourViewSet(viewsets.ModelViewSet):
    """Brief description of what this ViewSet manages."""

    queryset = YourModel.objects.all()
    serializer_class = YourSerializer
```

**For Custom Actions:**
```python
# If response is simple status message, use RESPONSE_WITH_STATUS
@action(detail=True, methods=["post"])
@extend_schema(
    summary="Vote for an item",
    description="Add a vote to support an item. Authenticated users can vote once.",
    request=None,
    responses={
        200: RESPONSE_WITH_STATUS,  # Use consolidated response
        201: RESPONSE_WITH_STATUS,
        400: OpenApiResponse(description="Already voted"),
        403: OpenApiResponse(description="Voting not allowed"),
    },
)
def vote(self, request, pk=None):
    pass


# For complex responses, extract to openapi.py as a constant
# In openapi.py:
# ACTION_RESPONSE = inline_serializer(
#     name='ActionResponse',
#     fields={
#         'status': serializers.CharField(),
#         'result': serializers.CharField(),
#     }
# )


@action(detail=True, methods=["post"])
@extend_schema(
    summary="Brief action description",
    description="Detailed explanation if logic is complex. Mention side effects.",
    request=None,  # Use None for no request body
    responses={
        200: ACTION_RESPONSE,  # Reference extracted serializer
        400: OpenApiResponse(description="Bad request reason"),
        404: OpenApiResponse(description="Not found reason"),
    },
)
def custom_action(self, request, pk=None):
    pass
```

**For Function-Based Views:**
```python
@extend_schema(
    operation_id="unique_operation_id",
    summary="Brief description",
    description="Detailed explanation",
    parameters=[...],
    request=RequestSerializer,  # or inline_serializer
    responses={200: ResponseSerializer},
    tags=["Category"],
)
@api_view(["GET", "POST"])
def your_view(request):
    pass
```

### 9. Documentation Checklist for Each Endpoint

Required:
- [ ] `summary` (imperative, <100 chars)
- [ ] `description` (if logic is non-trivial)
- [ ] Query parameters documented with types
- [ ] Request body schema (POST/PUT/PATCH)
- [ ] Success responses (200/201/204)
- [ ] Error responses (400/401/403/404)
- [ ] Side effects mentioned
- [ ] Authentication requirements clear
- [ ] No inline_serializer in decorators (all extracted to openapi.py)
- [ ] Identical response structures consolidated into single constant

### 10. Common Patterns

**Paginated List:**
```python
parameters = [
    OpenApiParameter("page", OpenApiTypes.INT, description="Page number"),
    OpenApiParameter(
        "page_size",
        OpenApiTypes.INT,
        description="Items per page (max 100)",
    ),
]
```

**Filters:**
```python
parameters = [
    OpenApiParameter(
        "status",
        OpenApiTypes.STR,
        enum=["active", "inactive", "archived"],
    ),
    OpenApiParameter("created_after", OpenApiTypes.DATE),
]
```

**Bulk Operation:**
```python
request = inline_serializer(
    name="BulkActionRequest",
    fields={
        "ids": serializers.ListField(child=serializers.IntegerField()),
        "action": serializers.ChoiceField(choices=["delete", "archive"]),
    },
),
responses = {
    200: inline_serializer(
        name="BulkActionResponse",
        fields={
            "success_count": serializers.IntegerField(),
            "failed_count": serializers.IntegerField(),
            "errors": serializers.DictField(),
        },
    ),
}
```

### 11. Validate and Test

Check known issues in the Troubleshooting section below.

Use the following commands to validate and test the schema:

```bash
docker compose run --rm django python manage.py spectacular --validate --fail-on-warn
docker compose run --rm django python manage.py spectacular --file openapi-schema.yaml --format openapi-yaml
```

IMPORTANT: These are the ONLY commands allowed to be used to validate and test the schema.
Do not use any other commands to validate and test the schema.

### 12. Completion Criteria

- [ ] Schema generates without errors/warnings
- [ ] All endpoints visible in /api-docs/
- [ ] All endpoints have human-readable titles and summaries
- [ ] Complex endpoints have descriptions
- [ ] All parameters documented with correct types
- [ ] Request/response schemas defined
- [ ] Error responses documented
- [ ] Manual testing of critical endpoints successful

## Quick Reference

**Import statement:**
```python
# In openapi.py (definitions file)
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    inline_serializer,
)
from rest_framework import serializers

# In view files (usage)
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from democracy.views.openapi import (
    PAGINATION_PARAMS,  # Import from openapi.py
    RESPONSE_WITH_STATUS,
)
```

**Note:** Never import `inline_serializer` in view files - all serializers should be defined in `openapi.py`

**Parameter types:** `OpenApiTypes.STR`, `INT`, `BOOL`, `DATE`, `DATETIME`, `UUID`, `FLOAT`, `BINARY`

**Parameter locations:** `OpenApiParameter.QUERY`, `.PATH`, `.HEADER`, `.COOKIE`

**Common response codes:** 200 (OK), 201 (Created), 204 (No Content), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 409 (Conflict), 422 (Unprocessable Entity), 500 (Server Error)

## Troubleshooting

**AttributeError: 'Request' object has no attribute 'accepted_renderer'**
- Ensure `DEFAULT_RENDERER_CLASSES` is set in REST_FRAMEWORK settings
- Use `getattr(request, 'accepted_renderer', None)` instead of direct access

**Endpoints not showing:**
- Check viewset is registered in router
- Verify `DEFAULT_SCHEMA_CLASS` is set
- Ensure URL patterns are included

**Schema validation fails:**
- Check decorator syntax
- Verify all referenced serializers exist
- Validate OpenApiParameter types

---

**Execute this command by following steps 1-12 sequentially. ALWAYS organize OpenAPI parameters in step 7 before adding decorators in step 8. Prioritize native DRF features (step 6) before explicit @extend_schema (step 8). Keep summaries concise, list ONLY the changes that were done.**
