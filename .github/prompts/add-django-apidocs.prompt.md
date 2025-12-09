# Add Django REST Framework OpenAPI Documentation

Complete setup and documentation of all API endpoints using drf-spectacular with Redoc and Swagger UI.

## Execution Steps

### 1. Install Dependencies

Add to `requirements.in`:
```txt
drf-spectacular
PyYAML>=6.0
```

Then install:
```bash
.venv/bin/pip install drf-spectacular PyYAML
```

### 2. Configure Settings

In `settings.py` or `settings/base.py`:

**Add to INSTALLED_APPS:**
```python
INSTALLED_APPS = [
    # ... existing apps
    'drf_spectacular',
    # ... your apps
]
```

**Add REST_FRAMEWORK config (REQUIRED):**
```python
REST_FRAMEWORK = {
    # ... existing settings
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [  # REQUIRED to prevent AttributeError
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}
```

**Add SPECTACULAR_SETTINGS:**
```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Your API Name',
    'DESCRIPTION': 'API description with authentication details',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_PATCH': True,
    'SCHEMA_PATH_PREFIX': r'/v1/',  # Adjust to match your API version pattern
    'SCHEMA_PATH_PREFIX_TRIM': True,
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
    path('api_docs/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api_docs/swagger_ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api_docs/schema/', SpectacularAPIView.as_view(), name='schema'),
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

# Good - safe for schema generation  
accepted_renderer = getattr(request, 'accepted_renderer', None)
if isinstance(accepted_renderer, SomeRenderer):
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

### 6. Document Each Endpoint

**For ViewSets:**
```python
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

@extend_schema_view(
    list=extend_schema(
        summary="List all items",
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, description='Filter by status', enum=['active', 'inactive']),
            OpenApiParameter('search', OpenApiTypes.STR, description='Search in name/description'),
            OpenApiParameter('ordering', OpenApiTypes.STR, description='Sort field (prefix - for desc)'),
        ],
    ),
    retrieve=extend_schema(summary="Get item by ID"),
    create=extend_schema(
        summary="Create new item",
        responses={
            201: YourSerializer,
            400: OpenApiResponse(description='Validation error'),
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
@action(detail=True, methods=['post'])
@extend_schema(
    summary="Brief action description",
    description="Detailed explanation if logic is complex. Mention side effects.",
    request=inline_serializer(
        name='ActionRequest',
        fields={
            'field': serializers.CharField(help_text='Field description'),
        }
    ),
    responses={
        200: inline_serializer(
            name='ActionResponse',
            fields={
                'status': serializers.CharField(),
                'result': serializers.CharField(),
            }
        ),
        400: OpenApiResponse(description='Bad request reason'),
        404: OpenApiResponse(description='Not found reason'),
    },
)
def custom_action(self, request, pk=None):
    pass
```

**For Function-Based Views:**
```python
@extend_schema(
    operation_id='unique_operation_id',
    summary="Brief description",
    description="Detailed explanation",
    parameters=[...],
    request=RequestSerializer,  # or inline_serializer
    responses={200: ResponseSerializer},
    tags=['Category'],
)
@api_view(['GET', 'POST'])
def your_view(request):
    pass
```

### 7. Documentation Checklist for Each Endpoint

Required:
- [ ] `summary` (imperative, <100 chars)
- [ ] `description` (if logic is non-trivial)
- [ ] Query parameters documented with types
- [ ] Request body schema (POST/PUT/PATCH)
- [ ] Success responses (200/201/204)
- [ ] Error responses (400/401/403/404)
- [ ] Side effects mentioned
- [ ] Authentication requirements clear

### 8. Common Patterns

**Paginated List:**
```python
parameters=[
    OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
    OpenApiParameter('page_size', OpenApiTypes.INT, description='Items per page (max 100)'),
]
```

**Filters:**
```python
parameters=[
    OpenApiParameter('status', OpenApiTypes.STR, enum=['active', 'inactive', 'archived']),
    OpenApiParameter('created_after', OpenApiTypes.DATE),
]
```

**Bulk Operation:**
```python
request=inline_serializer(
    name='BulkActionRequest',
    fields={
        'ids': serializers.ListField(child=serializers.IntegerField()),
        'action': serializers.ChoiceField(choices=['delete', 'archive']),
    }
),
responses={
    200: inline_serializer(
        name='BulkActionResponse',
        fields={
            'success_count': serializers.IntegerField(),
            'failed_count': serializers.IntegerField(),
            'errors': serializers.DictField(),
        }
    ),
}
```

### 9. Validate and Test

Check known issues in the Troubleshooting section below.

Use the following commands to validate and test the schema:

```bash
docker compose run --rm django python manage.py spectacular --validate --fail-on-warn
docker compose run --rm django python manage.py spectacular --file openapi-schema.yaml --format openapi-yaml
```

IMPORTANT: These are the ONLY commands allowed to be used to validate and test the schema.
Do not use any other commands to validate and test the schema.

### 10. Completion Criteria

- [ ] Schema generates without errors/warnings
- [ ] All endpoints visible in /api/docs/
- [ ] All endpoints have summaries
- [ ] Complex endpoints have descriptions
- [ ] All parameters documented with correct types
- [ ] Request/response schemas defined
- [ ] Error responses documented
- [ ] Manual testing of critical endpoints successful

## Quick Reference

**Import statement:**
```python
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
```

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

**Execute this command by following steps 1-10 sequentially. Focus on analyzing actual code implementation before writing documentation. Keep the final summary short and concise, list only the changes made.**
