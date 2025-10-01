from django.urls import path
from . import views

urlpatterns = [
    # Home and dashboard
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    
    # Authentication
    path("register/", views.register_view, name="register"),
    
    # Entry CRUD operations
    path("entries/", views.entry_list, name="entry_list"),
    path("entries/<int:pk>/", views.entry_detail, name="entry_detail"),
    path("entries/new/", views.entry_create, name="entry_create"),
    path("entries/<int:pk>/edit/", views.entry_edit, name="entry_edit"),
    path("entries/<int:pk>/delete/", views.entry_delete, name="entry_delete"),
    
    # Quick entry creation (for AJAX from dashboard)
    path("quick/win/", views.quick_add_win, name="quick_add_win"),
    path("quick/gratitude/", views.quick_add_gratitude, name="quick_add_gratitude"),
    
    # Category management
    path("categories/", views.category_list, name="category_list"),
    path("categories/new/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
]
