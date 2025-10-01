from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Count
from .models import Entry


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
