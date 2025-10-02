"""
URL configuration for Daily Wins Tracker project.

This is the main URL router that directs all requests to the appropriate views.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin interface for superuser management
    path('admin/', admin.site.urls),
    
    # All app URLs are handled by tracker.urls - includes auth, dashboard, entries, etc.
    path("", include("tracker.urls")),
    
    # Note: Django's built-in auth URLs are commented out because we use custom auth views
    # for better user experience and ADHD-friendly messaging
    # path('accounts/', include('django.contrib.auth.urls')),  
]
