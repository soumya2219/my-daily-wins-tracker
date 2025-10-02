from django.urls import path
from . import views

urlpatterns = [
    # Home and dashboard
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),  # Redirects to weekly
    path("weekly/", views.weekly_dashboard, name="weekly_dashboard"),
    
    # AJAX endpoints for weekly cards
    path("entry/<str:entry_date>/", views.entry_detail_modal, name="entry_detail_modal"),
    
    # Authentication
    path("register/", views.register_view, name="register"),
    path("login/", views.custom_login_view, name="login"),
    path("logout/", views.custom_logout_view, name="logout"),
    
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
    
    # AJAX endpoints for category management
    path("categories/ajax/create/", views.category_ajax_create, name="category_ajax_create"),
    path("categories/ajax/list/", views.category_ajax_list, name="category_ajax_list"),
    path("categories/<int:pk>/ajax/delete/", views.category_ajax_delete, name="category_ajax_delete"),
]
