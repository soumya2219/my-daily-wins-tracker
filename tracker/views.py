from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from datetime import date, timedelta, datetime
import json
from .models import Entry, Category
from .forms import EntryForm, QuickEntryForm, CategoryForm


def home(request):
    # Just redirect to dashboard if logged in, otherwise show home page
    if request.user.is_authenticated:
        return redirect('weekly_dashboard')
    return render(request, "home.html")


@login_required
def weekly_dashboard(request):
    # Get current week (Monday to Sunday)
    today = date.today()
    days_since_monday = today.weekday()  # Monday = 0, Sunday = 6
    week_start = today - timedelta(days=days_since_monday)
    
    # Allow navigation to different weeks
    week_offset = request.GET.get('week', 0)
    try:
        week_offset = int(week_offset)
    except (ValueError, TypeError):
        week_offset = 0
    
    # Calculate the target week
    target_week_start = week_start + timedelta(weeks=week_offset)
    
    # Generate 7 days for the week
    week_days = []
    for i in range(7):
        day_date = target_week_start + timedelta(days=i)
        
        # Get entry for this day (if exists)
        try:
            entry = Entry.objects.get(user=request.user, entry_date=day_date)
        except Entry.DoesNotExist:
            entry = None
        
        week_days.append({
            'date': day_date,
            'day_name': day_date.strftime('%A'),
            'day_short': day_date.strftime('%a'),
            'day_number': day_date.day,
            'entry': entry,
            'is_today': day_date == today,
            'is_past': day_date < today,
            'is_future': day_date > today,
        })
    
    # Week navigation
    prev_week = week_offset - 1
    next_week = week_offset + 1
    current_week_label = target_week_start.strftime('%B %d, %Y')
    
    # Basic stats for the week
    week_end = target_week_start + timedelta(days=6)
    week_entries = Entry.objects.filter(
        user=request.user,
        entry_date__range=[target_week_start, week_end]
    )
    
    week_stats = {
        'entries_count': week_entries.count(),
        'avg_mood': None,
        'mood_trend': None,
    }
    
    # Calculate average mood for the week
    mood_entries = week_entries.filter(mood_rating__isnull=False)
    if mood_entries.exists():
        total_mood = sum(entry.mood_rating for entry in mood_entries)
        week_stats['avg_mood'] = round(total_mood / mood_entries.count(), 1)
    
    context = {
        'week_days': week_days,
        'week_start': target_week_start,
        'week_label': current_week_label,
        'prev_week': prev_week,
        'next_week': next_week,
        'week_stats': week_stats,
        'is_current_week': week_offset == 0,
    }
    return render(request, 'tracker/weekly_dashboard.html', context)


@login_required
def dashboard(request):
    # redirect to weekly view
    return redirect('weekly_dashboard')


@login_required
def entry_detail_modal(request, entry_date):
    # Get or create entry for specific date 
    # TODO: add better error handling here
    try:
        target_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get existing entry or create new one
    entry, created = Entry.objects.get_or_create(
        user=request.user,
        entry_date=target_date,
        defaults={
            'title': '',
            'content': '',
            'gratitude_text': '',
        }
    )
    
    if request.method == 'POST':
        form = EntryForm(request.POST, instance=entry, user=request.user)
        if form.is_valid():
            entry = form.save()
            return JsonResponse({
                'success': True,
                'entry': {
                    'id': entry.id,
                    'title': entry.title,
                    'content': entry.content,
                    'gratitude_text': entry.gratitude_text,
                    'mood_rating': entry.mood_rating,
                    'mood_emoji': entry.mood_emoji,
                    'has_content': entry.has_content,
                    'date': entry.entry_date.strftime('%Y-%m-%d'),
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    else:
        form = EntryForm(instance=entry, user=request.user)
    
    # Return HTML for the modal
    from django.template.loader import render_to_string
    modal_html = render_to_string('tracker/entry_modal.html', {
        'form': form,
        'entry': entry,
        'entry_date': target_date,
        'created': created,
    }, request=request)
    
    return JsonResponse({
        'html': modal_html,
        'entry': {
            'id': entry.id,
            'title': entry.title,
            'content': entry.content,
            'gratitude_text': entry.gratitude_text,
            'mood_rating': entry.mood_rating,
            'mood_emoji': entry.mood_emoji,
            'has_content': entry.has_content,
            'date': entry.entry_date.strftime('%Y-%m-%d'),
        }
    })


def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('weekly_dashboard')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            
            # Auto-login the user after registration
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def custom_login_view(request):
    """Custom login view with better UX"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Django's built-in LoginView will handle the actual login
    # This is just for custom context if needed
    return render(request, 'registration/login.html')


# ================================
# ENTRY CRUD OPERATIONS
# ================================

@login_required
def entry_list(request):
    """List all entries for the current user with filtering and pagination"""
    entries = Entry.objects.filter(user=request.user)
    
    # Filter by content type if requested
    entry_type_filter = request.GET.get('type')
    if entry_type_filter == 'win':
        # Show entries that have content (wins)
        entries = entries.exclude(content__exact='')
    elif entry_type_filter == 'gratitude':
        # Show entries that have gratitude text
        entries = entries.exclude(gratitude_text__exact='')
    
    # Filter by category if requested
    category_filter = request.GET.get('category')
    if category_filter:
        try:
            category_id = int(category_filter)
            entries = entries.filter(categories__id=category_id)
        except (ValueError, TypeError):
            pass
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        entries = entries.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query)
        )
    
    # Order by date (newest first)
    entries = entries.distinct().order_by('-date_created')
    
    # Pagination
    paginator = Paginator(entries, 10)  # 10 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user's categories for filter dropdown
    user_categories = Category.objects.filter(user=request.user)
    
    context = {
        'page_obj': page_obj,
        'entries': page_obj,  # For template compatibility
        'user_categories': user_categories,
        'current_filter': entry_type_filter,
        'current_category': category_filter,
        'search_query': search_query or '',
        'total_count': entries.count(),
    }
    return render(request, 'tracker/entry_list.html', context)


@login_required
def entry_detail(request, pk):
    entry = get_object_or_404(Entry, pk=pk, user=request.user)
    return render(request, 'tracker/entry_detail.html', {'entry': entry})


@login_required
def entry_create(request):
    # Get entry type from URL parameter for UI display purposes
    entry_type = request.GET.get('type', 'win')  # Default to win for display
    
    if request.method == 'POST':
        form = EntryForm(request.POST, user=request.user)
        if form.is_valid():
            entry = form.save()
            messages.success(
                request, 
                '🎉 Your daily entry has been saved!'
            )
            return redirect('entry_detail', pk=entry.pk)
    else:
        # Create form without pre-populating entry_type since it no longer exists
        form = EntryForm(user=request.user)
    
    context = {
        'form': form,
        'entry_type': entry_type,
        'is_editing': False,
    }
    return render(request, 'tracker/entry_form.html', context)


@login_required
def entry_edit(request, pk):
    entry = get_object_or_404(Entry, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = EntryForm(request.POST, instance=entry, user=request.user)
        if form.is_valid():
            entry = form.save()
            messages.success(request, '✅ Your entry has been updated!')
            return redirect('entry_detail', pk=entry.pk)
    else:
        form = EntryForm(instance=entry, user=request.user)
    
    context = {
        'form': form,
        'entry': entry,
        'entry_type': 'win',  # Default for display, since entry_type field no longer exists
        'is_editing': True,
    }
    return render(request, 'tracker/entry_form.html', context)


@login_required
def entry_delete(request, pk):
    """Delete an entry with confirmation"""
    entry = get_object_or_404(Entry, pk=pk, user=request.user)
    
    if request.method == 'POST':
        entry_title = entry.title
        entry.delete()
        messages.success(request, f'🗑️ "{entry_title}" has been deleted.')
        return redirect('entry_list')
    
    return render(request, 'tracker/entry_confirm_delete.html', {'entry': entry})


@login_required
def quick_add_win(request):
    """Quick add a win from dashboard"""
    if request.method == 'POST':
        form = QuickEntryForm(
            request.POST, 
            user=request.user
        )
        if form.is_valid():
            entry = form.save()
            messages.success(request, f'🏆 Win "{entry.title}" added!')
            
            # check if its ajax
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': f'🏆 Win "{entry.title}" added!',
                    'entry_id': entry.pk
                })
            
            return redirect('dashboard')
    
    # redirect to dashboard if form not valid or GET request
    if not form.is_valid():
        for error in form.errors.values():
            messages.error(request, f'Error: {error[0]}')
    
    return redirect('dashboard')


@login_required
def quick_add_gratitude(request):
    """Quick add gratitude from dashboard"""
    if request.method == 'POST':
        form = QuickEntryForm(
            request.POST, 
            user=request.user
        )
        if form.is_valid():
            entry = form.save()
            messages.success(request, f'🙏 Gratitude "{entry.title}" added!')
            
            # Return JSON for AJAX requests
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': f'🙏 Gratitude "{entry.title}" added!',
                    'entry_id': entry.pk
                })
            
            return redirect('dashboard')
    
    # For GET requests or form errors, redirect to dashboard
    if not form.is_valid():
        for error in form.errors.values():
            messages.error(request, f'Error: {error[0]}')
    
    return redirect('dashboard')


# ================================
# CATEGORY MANAGEMENT
# ================================

@login_required
def category_list(request):
    """List all categories for the current user"""
    categories = Category.objects.filter(user=request.user)
    
    # Add entry count for each category
    categories = categories.annotate(
        entry_count=Count('entries', filter=Q(entries__user=request.user))
    )
    
    return render(request, 'tracker/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST, user=request.user)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'🏷️ Category "{category.name}" created!')
            return redirect('category_list')
    else:
        form = CategoryForm(user=request.user)
    
    context = {
        'form': form,
        'is_editing': False,
    }
    return render(request, 'tracker/category_form.html', context)


@login_required
def category_edit(request, pk):
    """Edit an existing category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'✅ Category "{category.name}" updated!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category, user=request.user)
    
    context = {
        'form': form,
        'category': category,
        'is_editing': True,
    }
    return render(request, 'tracker/category_form.html', context)


@login_required
def category_delete(request, pk):
    """Delete a category with confirmation"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'🗑️ Category "{category_name}" has been deleted.')
        return redirect('category_list')
    
    # Get entry count for confirmation message
    entry_count = category.entries.filter(user=request.user).count()
    
    return render(request, 'tracker/category_confirm_delete.html', {
        'category': category,
        'entry_count': entry_count
    })


# AJAX ENDPOINTS FOR CATEGORY MANAGEMENT

@login_required
def category_ajax_create(request):
    """Create a category via AJAX"""
    if request.method == 'POST':
        try:
            # Handle FormData from the frontend
            form = CategoryForm(request.POST, user=request.user)
            
            if form.is_valid():
                category = form.save()
                return JsonResponse({
                    'success': True,
                    'category': {
                        'id': category.id,
                        'name': category.name,
                        'color': category.color
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid form data',
                    'errors': form.errors
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def category_ajax_list(request):
    """Get user's categories via AJAX"""
    categories = Category.objects.filter(user=request.user).values('id', 'name', 'color')
    return JsonResponse({
        'success': True,
        'categories': list(categories)
    })


@login_required
def category_ajax_delete(request, pk):
    """Delete a category via AJAX"""
    if request.method == 'DELETE':
        try:
            category = get_object_or_404(Category, pk=pk, user=request.user)
            category_name = category.name
            category.delete()
            return JsonResponse({
                'success': True,
                'message': f'Category "{category_name}" deleted successfully'
            })
        except Category.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Category not found'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
