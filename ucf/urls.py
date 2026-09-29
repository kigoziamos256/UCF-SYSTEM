from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from members import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Allauth (Google + account URLs) — must be at ROOT
    path('accounts/', include('allauth.urls')),

    # PWA (manifest, service worker, etc.)
    path('', include('pwa.urls')),

    # App URLs
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('members/', include('members.urls')),
]

# Serve media files in development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
