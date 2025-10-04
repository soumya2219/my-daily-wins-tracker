from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from .validators import validate_username
from .auth_forms import CustomUserCreationForm
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from datetime import date, timedelta, datetime
import calendar
import json
from .models import Entry, Category, StickyNote


# Authentication Views
from .forms import EntryForm, QuickEntryForm, CategoryForm


def home(request):
    """Landing page - redirect to dashboard if logged in"""
    if request.user.is_authenticated:
        return redirect('weekly_dashboard')
    return render(request, "home.html")


@login_required
def weekly_dashboard(request):
    """Main weekly dashboard view"""
    # Current week calculation (Monday-Sunday)
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
    
    # Only count entries that actually have content
    week_entries_with_content = week_entries.filter(
        Q(title__isnull=False, title__gt='') |
        Q(content__isnull=False, content__gt='') |
        Q(gratitude_text__isnull=False, gratitude_text__gt='') |
        Q(mood_rating__isnull=False)
    )
    
    week_stats = {
        'entries_count': week_entries_with_content.count(),
        'avg_mood': None,
        'mood_trend': None,
    }
    
    # Calculate average mood for the week
    mood_entries = week_entries.filter(mood_rating__isnull=False)
    if mood_entries.exists():
        total_mood = sum(entry.mood_rating for entry in mood_entries)
        week_stats['avg_mood'] = round(total_mood / mood_entries.count(), 1)

    # Generate calendar for current month
    today = date.today()
    cal = calendar.Calendar(firstweekday=0)  # Monday is first day
    month_days = cal.monthdayscalendar(today.year, today.month)
    
    # Get all user entries for current month to highlight days with entries
    month_start = date(today.year, today.month, 1)
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
    
    month_entries = Entry.objects.filter(
        user=request.user,
        entry_date__range=[month_start, month_end]
    )
    entry_dates = set(month_entries.values_list('entry_date', flat=True))
    
    # Build calendar data with entry information
    calendar_weeks = []
    for week in month_days:
        calendar_week = []
        for day in week:
            if day == 0:
                calendar_week.append({
                    'day': '',
                    'is_today': False,
                    'has_entry': False,
                    'date': None
                })
            else:
                day_date = date(today.year, today.month, day)
                calendar_week.append({
                    'day': day,
                    'is_today': day_date == today,
                    'has_entry': day_date in entry_dates,
                    'date': day_date
                })
        calendar_weeks.append(calendar_week)
    
    month_name = today.strftime('%B %Y')

    context = {
        'week_days': week_days,
        'week_start': target_week_start,
        'week_label': current_week_label,
        'prev_week': prev_week,
        'next_week': next_week,
        'week_stats': week_stats,
        'is_current_week': week_offset == 0,
        'calendar_weeks': calendar_weeks,
        'month_name': month_name,
        'calendar_month': today.month - 1,  # JavaScript months are 0-indexed
        'calendar_year': today.year,
        'sticky_notes': request.user.sticky_notes.all()[:6],  # Limit to 6 notes for UI
    }
    return render(request, 'tracker/weekly_dashboard.html', context)


@login_required
def dashboard(request):
    # redirect to weekly view
    return redirect('weekly_dashboard')


@login_required
def entry_detail_modal(request, entry_date):
    """
    The popup modal when you click on a day in the calendar.
    Handles both showing existing entries and creating new ones.
    Uses AJAX so the page doesn't reload.
    """
    # Make sure the date is valid
    try:
        target_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get the entry for this day, or make a blank one if it doesn't exist
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
        # Someone submitted the form
        form = EntryForm(request.POST, instance=entry, user=request.user)
        if form.is_valid():
            entry = form.save()
            # Send back success response
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
    """
    Sign up page with our custom form that's friendlier for ADHD folks.
    Auto-logs people in after they register so they don't have to do it twice.
    """
    # If already logged in, just go to dashboard
    if request.user.is_authenticated:
        return redirect('weekly_dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            
            # Log them in automatically - one less step
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def custom_login_view(request):
    """Custom login view with notifications"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}! You are now logged in. 🎉')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})


def custom_logout_view(request):
    """Custom logout view with notifications"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Goodbye, {username}! You have been logged out successfully. 👋')
    return redirect('home')


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


@login_required
def get_calendar_data(request):
    """AJAX view to get calendar data for a specific month"""
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    today = date.today()
    
    cal = calendar.Calendar(firstweekday=0)  # Monday is first day
    month_days = cal.monthdayscalendar(year, month)
    
    # Get entries for the requested month
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    
    month_entries = Entry.objects.filter(
        user=request.user,
        entry_date__range=[month_start, month_end]
    )
    entry_dates = set(month_entries.values_list('entry_date', flat=True))
    
    # Generate HTML for calendar grid
    calendar_html = ""
    for week in month_days:
        calendar_html += '<div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; margin-bottom: 2px;">'
        for day in week:
            if day == 0:
                calendar_html += '<div class="calendar-day-compact calendar-empty-compact"></div>'
            else:
                day_date = date(year, month, day)
                classes = ['calendar-day-compact']
                onclick = ""
                
                if day_date == today:
                    classes.append('calendar-today-compact')
                if day_date in entry_dates:
                    classes.append('calendar-has-entry-compact')
                    onclick = f'onclick="showDayEntry(\'{day_date.strftime("%Y-%m-%d")}\'))"'
                
                calendar_html += f'''
                    <div class="{' '.join(classes)}" {onclick}>
                        {day}
                        {'<span class="entry-dot-compact">●</span>' if day_date in entry_dates else ''}
                    </div>
                '''
        calendar_html += '</div>'
    
    month_name = date(year, month, 1).strftime('%B %Y')
    
    return JsonResponse({
        'calendar_html': calendar_html,
        'month_name': month_name
    })


@login_required
def get_day_entry(request):
    """AJAX view to get entry details for a specific day"""
    date_str = request.GET.get('date')
    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        entry = Entry.objects.get(user=request.user, entry_date=entry_date)
        
        return JsonResponse({
            'entry': {
                'title': entry.title,
                'description': entry.content,
                'mood_rating': entry.mood_rating,
                'category': entry.category.name if entry.category else None,
                'date': entry.entry_date.strftime('%B %d, %Y'),
                'created_at': entry.created_at.strftime('%B %d, %Y at %I:%M %p'),
            }
        })
    except (Entry.DoesNotExist, ValueError):
        return JsonResponse({'entry': None})


@login_required
def sticky_note_create(request):
    """AJAX view to create a new sticky note"""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            # Get next order number
            last_note = request.user.sticky_notes.order_by('-order').first()
            next_order = (last_note.order + 1) if last_note else 0
            
            note = StickyNote.objects.create(
                user=request.user,
                content=content,
                order=next_order
            )
            
            return JsonResponse({
                'success': True,
                'note': {
                    'id': note.id,
                    'content': note.content,
                    'created_at': note.created_at.strftime('%B %d, %Y at %I:%M %p'),
                }
            })
        else:
            return JsonResponse({'success': False, 'error': 'Content cannot be empty'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def sticky_note_update(request, note_id):
    """AJAX view to update sticky note content"""
    if request.method == 'POST':
        try:
            note = StickyNote.objects.get(id=note_id, user=request.user)
            content = request.POST.get('content', '').strip()
            
            if content:
                note.content = content
                note.save()
                return JsonResponse({'success': True})
            else:
                # If content is empty, delete the note
                note.delete()
                return JsonResponse({'success': True, 'deleted': True})
                
        except StickyNote.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Note not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def sticky_note_complete(request, note_id):
    """AJAX view to complete a sticky note and convert it to a win"""
    if request.method == 'POST':
        try:
            note = StickyNote.objects.get(id=note_id, user=request.user)
            entry = note.complete_as_win()
            
            return JsonResponse({
                'success': True,
                'entry': {
                    'title': entry.title,
                    'date': entry.entry_date.strftime('%B %d, %Y'),
                }
            })
            
        except StickyNote.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Note not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def sticky_note_delete(request, note_id):
    """AJAX view to delete a sticky note"""
    if request.method == 'DELETE':
        try:
            note = StickyNote.objects.get(id=note_id, user=request.user)
            note.delete()
            return JsonResponse({'success': True})
            
        except StickyNote.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Note not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
