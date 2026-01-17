# Add Django REST Framework OpenAPI Documentation

Setup and document all API endpoints using drf-spectacular. Execute steps 1-12 sequentially.

## Critical Rules

1. **Use actual serializer classes, NEVER strings** (`request=MySerializer` not `request="MySerializer"`)
2. **Consolidate identical response structures** (one `RESPONSE_WITH_STATUS`, not multiple)
3. **All `inline_serializer` go in `openapi.py`**, never in view files
4. **Organize `openapi.py` BEFORE adding decorators**

## Steps

### 1. Install

Add to `requirements.in`:
```txt
drf-spectacular
```

Install:
```bash
.venv/bin/pip install drf-spectacular
```

### 2. Configure Settings

In `settings/base.py`, add to `INSTALLED_APPS`:
```python
"drf_spectacular",
```

Add/update `REST_FRAMEWORK`:
```python
REST_FRAMEWORK = {
    # ... existing settings
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [  # Required for schema generation
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}
```

Add `SPECTACULAR_SETTINGS`:
```python
SPECTACULAR_SETTINGS = {
    "TITLE": "API Name",
    "DESCRIPTION": "API description",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_PATCH": True,
    "SCHEMA_PATH_PREFIX": r"/v1/",  # Adjust to match API version
    "SCHEMA_PATH_PREFIX_TRIM": True,
}
```

### 3. Update URL Routes

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
]
```

### 4. Fix Compatibility

Search for unsafe `request.accepted_renderer` usage:
```bash
grep -r "request\.accepted_renderer" --include="*.py" .
```

Replace with safe pattern:
```python
# Before:
if isinstance(request.accepted_renderer, SomeRenderer):

# After:
accepted_renderer = getattr(request, "accepted_renderer", None)
if isinstance(accepted_renderer, SomeRenderer):
```

### 5. Inventory Endpoints

Find all views containing:
- `viewsets.ModelViewSet` / `viewsets.ViewSet`
- `APIView` classes
- `@api_view` decorators
- `@action` decorators

List: HTTP methods, URL patterns, view names, file locations.

### 6. Add Native Documentation (Priority)

drf-spectacular auto-documents:

1. **Model/Serializer `help_text`**:
```python
title = models.CharField(max_length=255, help_text="Hearing title")
n_comments = serializers.SerializerMethodField(help_text="Total comments")
```

2. **FilterSet `help_text`**:
```python
title = django_filters.CharFilter(
    lookup_expr="icontains",
    help_text="Filter by title (case-insensitive)",
)
```

3. **Docstrings** (ViewSets, actions):
```python
class HearingViewSet(viewsets.ModelViewSet):
    """Manage participatory democracy hearings."""

    def list(self, request, *args, **kwargs):
        """List all hearings with filtering and pagination."""
```

4. **Enum docstrings**:
```python
class Commenting(Enum):
    """Commenting modes: NONE, REGISTERED, OPEN, STRONG."""
```

**Implementation order:**
1. FilterSet `help_text`
2. Model field `help_text`
3. Serializer field `help_text`
4. ViewSet/action docstrings (concise)
5. Enum docstrings (concise)

**Use `@extend_schema` only for:**
- Complex schemas not in serializers
- Custom error responses
- Non-obvious side effects

### 7. Create/Update openapi.py (BEFORE decorators)

Create `/democracy/views/openapi.py`:
```python
"""Shared OpenAPI definitions. All inline_serializer go here."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, inline_serializer
from rest_framework import serializers

# Pagination
PAGINATION_PARAMS = [
    OpenApiParameter("limit", OpenApiTypes.INT,
                     description="Results per page"),
    OpenApiParameter("offset", OpenApiTypes.INT,
                     description="Offset for pagination"),
]

# Common responses - consolidate identical structures
RESPONSE_WITH_STATUS = inline_serializer(
    name="StatusResponse",
    fields={"status": serializers.CharField()},
)

# Add more as needed
```

**View-specific params stay in view files.**

### 8. Add @extend_schema Decorators

**ViewSets:**
```python
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from democracy.views.openapi import PAGINATION_PARAMS, RESPONSE_WITH_STATUS
from .serializers import MySerializer, MyCreateSerializer  # Import classes


@extend_schema_view(
    list=extend_schema(
        summary="List items",
        parameters=PAGINATION_PARAMS + [
            OpenApiParameter("status", OpenApiTypes.STR,
                             enum=["active", "inactive"]),
        ],
    ),
    retrieve=extend_schema(summary="Get item by ID"),
    create=extend_schema(
        summary="Create item",
        request=MyCreateSerializer,  # Actual class
        responses={
            201: MyCreateSerializer,  # Actual class
            400: OpenApiResponse(description="Validation error"),
        },
    ),
    update=extend_schema(
        summary="Update item",
        request=MyCreateSerializer,
        responses={200: MyCreateSerializer},
    ),
    partial_update=extend_schema(
        summary="Partially update item",
        request=MyCreateSerializer,
        responses={200: MyCreateSerializer},
    ),
    destroy=extend_schema(summary="Delete item"),
)
class MyViewSet(viewsets.ModelViewSet):
    """Brief description."""
```

**Custom Actions:**
```python
from democracy.views.openapi import RESPONSE_WITH_STATUS

@action(detail=True, methods=["post"])
@extend_schema(
    summary="Vote for item",
    request=None,
    responses={
        200: RESPONSE_WITH_STATUS,
        400: OpenApiResponse(description="Already voted"),
    },
)
def vote(self, request, pk=None):
    pass
```

**Function Views:**
```python
from .serializers import RequestSerializer, ResponseSerializer

@extend_schema(
    summary="Brief description",
    request=RequestSerializer,  # Actual class
    responses={200: ResponseSerializer},  # Actual class
)
@api_view(["POST"])
def my_view(request):
    pass
```

### 9. Validation Checklist

Per endpoint:
- [ ] Summary (<100 chars, imperative)
- [ ] Description (if non-trivial)
- [ ] Query params with types
- [ ] Request body (POST/PUT/PATCH) uses actual class
- [ ] Responses use actual classes (not strings)
- [ ] Success responses (200/201/204)
- [ ] Error responses (400/401/403/404)
- [ ] Side effects mentioned
- [ ] Auth requirements clear
- [ ] No `inline_serializer` in decorators
- [ ] Identical responses consolidated

### 10. Validate Schema

Run these commands:
```bash
docker compose run --rm django python manage.py spectacular --validate --fail-on-warn
docker compose run --rm django python manage.py spectacular --file openapi-schema.yaml --format openapi-yaml
```

**ONLY use these commands for validation.**

### 11. Run Pre-commit

After all steps complete:
```bash
pre-commit run --all-files
```

Fix any linting errors, if found.

### 12. Verify

- [ ] Schema generates without errors/warnings
- [ ] All endpoints visible in openapi schema file (openapi-schema.yaml)
- [ ] Parameters documented
- [ ] Request/response schemas correct

## Quick Reference

**Imports (view files):**
```python
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from democracy.views.openapi import PAGINATION_PARAMS, RESPONSE_WITH_STATUS
```

**Types:** `OpenApiTypes.STR`, `INT`, `BOOL`, `DATE`, `DATETIME`, `UUID`
**Locations:** `OpenApiParameter.QUERY`, `.PATH`, `.HEADER`
**Codes:** 200, 201, 204, 400, 401, 403, 404, 409, 422

## Troubleshooting

**AttributeError: 'Request' has no 'accepted_renderer'**
→ Add `DEFAULT_RENDERER_CLASSES` to `REST_FRAMEWORK` settings

**Warning: could not resolve "YourSerializer"**
→ Using string instead of class. Import and use actual class.

**Endpoints not showing**
→ Check viewset registered, `DEFAULT_SCHEMA_CLASS` set, URLs included

**Schema validation fails**
→ Check imports, no string serializer refs, correct param types

---

**Execute steps 1-12 sequentially. Organize openapi.py (step 7) BEFORE decorators (step 8). List ONLY changes made.**
