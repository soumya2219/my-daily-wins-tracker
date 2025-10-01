from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Entry, Category
from .forms import EntryForm, QuickEntryForm, CategoryForm


def home(request):
    """Public home page - shows welcome or redirects logged-in users to dashboard"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, "home.html")


@login_required
def dashboard(request):
    """User dashboard - shows their recent entries and stats"""
    # Get user's recent entries
    recent_entries = Entry.objects.filter(user=request.user)[:5]
    
    # Get some basic stats
    total_entries = Entry.objects.filter(user=request.user).count()
    total_wins = Entry.objects.filter(user=request.user, entry_type=Entry.EntryType.WIN).count()
    total_gratitude = Entry.objects.filter(user=request.user, entry_type=Entry.EntryType.GRATITUDE).count()
    
    # Recent mood average (if they've been rating mood)
    recent_mood_avg = None
    mood_entries = Entry.objects.filter(
        user=request.user, 
        mood_rating__isnull=False
    ).order_by('-date_created')[:10]
    
    if mood_entries:
        total_mood = sum(entry.mood_rating for entry in mood_entries)
        recent_mood_avg = round(total_mood / len(mood_entries), 1)
    
    context = {
        'recent_entries': recent_entries,
        'total_entries': total_entries,
        'total_wins': total_wins,
        'total_gratitude': total_gratitude,
        'recent_mood_avg': recent_mood_avg,
    }
    return render(request, 'tracker/dashboard.html', context)


def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
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
    
    # Filter by entry type if requested
    entry_type_filter = request.GET.get('type')
    if entry_type_filter in [Entry.EntryType.WIN, Entry.EntryType.GRATITUDE]:
        entries = entries.filter(entry_type=entry_type_filter)
    
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
    """View a single entry in detail"""
    entry = get_object_or_404(Entry, pk=pk, user=request.user)
    return render(request, 'tracker/entry_detail.html', {'entry': entry})


@login_required
def entry_create(request):
    """Create a new entry (either win or gratitude)"""
    # Get entry type from URL parameter or form
    entry_type = request.GET.get('type')
    if entry_type not in [Entry.EntryType.WIN, Entry.EntryType.GRATITUDE]:
        entry_type = Entry.EntryType.WIN  # Default to win
    
    if request.method == 'POST':
        form = EntryForm(request.POST, user=request.user)
        if form.is_valid():
            entry = form.save()
            messages.success(
                request, 
                f'🎉 Your {entry.get_entry_type_display().lower()} has been saved!'
            )
            return redirect('entry_detail', pk=entry.pk)
    else:
        # Pre-populate form with entry type
        initial_data = {'entry_type': entry_type}
        form = EntryForm(initial=initial_data, user=request.user)
    
    context = {
        'form': form,
        'entry_type': entry_type,
        'is_editing': False,
    }
    return render(request, 'tracker/entry_form.html', context)


@login_required
def entry_edit(request, pk):
    """Edit an existing entry"""
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
        'entry_type': entry.entry_type,
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
            user=request.user, 
            entry_type=Entry.EntryType.WIN
        )
        if form.is_valid():
            entry = form.save()
            messages.success(request, f'🏆 Win "{entry.title}" added!')
            
            # Return JSON for AJAX requests
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': f'🏆 Win "{entry.title}" added!',
                    'entry_id': entry.pk
                })
            
            return redirect('dashboard')
    
    # For GET requests or form errors, redirect to dashboard
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
            user=request.user, 
            entry_type=Entry.EntryType.GRATITUDE
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
