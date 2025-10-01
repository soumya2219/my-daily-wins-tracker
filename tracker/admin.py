from django.contrib import admin
from .models import Entry, Category


@admin.register(Category)  
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'color', 'date_created']
    list_filter = ['date_created', 'user']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['date_created']


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'entry_date', 'user', 'mood_rating', 'date_created']
    list_filter = ['entry_date', 'mood_rating', 'date_created', 'user']
    search_fields = ['title', 'content', 'gratitude_text', 'user__username']
    readonly_fields = ['date_created', 'date_modified']
    filter_horizontal = ('categories',)  # Nice widget for many-to-many
    
    fieldsets = (
        ('Entry Details', {
            'fields': ('user', 'entry_date', 'title', 'content')
        }),
        ('Mood & Gratitude', {
            'fields': ('mood_rating', 'gratitude_text', 'categories')
        }),
        ('Settings', {
            'fields': ('is_private',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_created', 'date_modified'),
            'classes': ('collapse',)
        }),
    )
