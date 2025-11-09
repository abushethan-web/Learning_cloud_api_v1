"""
URL configuration for Learning Cloud project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def root_redirect(request):
    """Redirect root URL to API documentation."""
    return HttpResponseRedirect('/api/docs/')


def api_info(request):
    """Return API information and available endpoints."""
    return JsonResponse({
        "message": "Learning Cloud API",
        "version": "1.0.0",
        "documentation": {
            "swagger_ui": "/api/docs/",
            "redoc": "/api/redoc/",
            "schema": "/api/schema/"
        },
        "endpoints": {
            "authentication": "/api/auth/",
            "accounts": "/api/profile/",
            "content": "/api/subjects/",
            "quizzes": "/api/quizzes/",
            "progress": "/api/progress/",
            "analytics": "/api/analytics/",
            "notifications": "/api/notifications/"
        },
        "note": "All API endpoints are prefixed with /api/"
    })


urlpatterns = [
    # Root endpoints
    path('', root_redirect, name='root'),
    path('health/', lambda request: JsonResponse({"status": "ok"})),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # OAuth2 (must come before other api/ routes to avoid conflicts)
    path('api/auth/', include('oauth2_provider.urls')),
    
    # API Documentation (specific routes first)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints (must come after specific routes)
    path('api/', include('apps.accounts.urls')),
    path('api/', include('apps.content.urls')),
    path('api/', include('apps.quizzes.urls')),
    path('api/', include('apps.progress.urls')),
    path('api/', include('apps.analytics.urls')),
    path('api/', include('apps.notifications.urls')),
    
    # API info endpoint (catch-all for /api/ - must be last)
    path('api/', api_info, name='api_info'),
    
    # Webhooks
    path('webhooks/', include('apps.webhook_urls')),
]

# Note: i18n_patterns removed to avoid URL conflicts
# All API endpoints are accessible via /api/ prefix

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


