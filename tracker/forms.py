from django import forms
from django.core.exceptions import ValidationError
from .models import Entry, Category


class EntryForm(forms.ModelForm):
    """Form for creating and editing daily entries with wins, mood, and gratitude"""
    
    class Meta:
        model = Entry
        fields = ['entry_date', 'title', 'content', 'mood_rating', 'gratitude_text', 'categories']
        widgets = {
            'entry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Summary of today (e.g., "Productive day at work")',
                'maxlength': 200
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'List your wins here:\n• Completed project milestone\n• Had a great conversation with a friend\n• Learned something new\n• Made healthy choices...',
                'rows': 5
            }),
            'mood_rating': forms.Select(attrs={
                'class': 'form-select'
            }),
            'gratitude_text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Today I was grateful for...',
                'rows': 3
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'entry_date': 'Which date is this entry for?',
            'title': 'A short summary of your day (optional)',
            'content': 'List all your wins and achievements for the day',
            'mood_rating': 'How was your overall mood today?',
            'gratitude_text': 'What are you grateful for today?',
            'categories': 'Optional: organize this entry with categories'
        }

    def __init__(self, *args, **kwargs):
        # Extract user from kwargs to filter categories
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter categories to only show user's own categories
        if self.user:
            self.fields['categories'].queryset = Category.objects.filter(user=self.user)
        else:
            self.fields['categories'].queryset = Category.objects.none()
        
        # Make categories field optional
        self.fields['categories'].required = False
        
        # Set default date to today if creating new entry
        if not self.instance.pk:
            from datetime import date
            self.fields['entry_date'].initial = date.today()

    def clean(self):
        cleaned_data = super().clean()
        mood_rating = cleaned_data.get('mood_rating')
        title = cleaned_data.get('title')
        content = cleaned_data.get('content')
        gratitude_text = cleaned_data.get('gratitude_text')
        
        # Ensure at least some content is provided
        if not any([title, content, gratitude_text, mood_rating]):
            raise ValidationError(
                'Please provide at least a title, content, gratitude note, or mood rating.'
            )
        
        # Validate meaningful content length
        if title and len(title.strip()) < 3:
            raise ValidationError({
                'title': 'Title must be at least 3 characters long.'
            })
        
        if content and len(content.strip()) < 5:
            raise ValidationError({
                'content': 'Content should be at least 5 characters long.'
            })
        
        if gratitude_text and len(gratitude_text.strip()) < 5:
            raise ValidationError({
                'gratitude_text': 'Gratitude note should be at least 5 characters long.'
            })
        
        return cleaned_data

    def save(self, commit=True):
        entry = super().save(commit=False)
        
        # Set the user if provided
        if self.user and not entry.user_id:
            entry.user = self.user
        
        if commit:
            entry.save()
            # Save many-to-many categories
            self.save_m2m()
        
        return entry


class QuickEntryForm(forms.ModelForm):
    """Simplified form for quick daily entry creation"""
    
    class Meta:
        model = Entry
        fields = ['title', 'content', 'mood_rating']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quick win title...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'What happened today?'
            }),
            'mood_rating': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.entry_date = kwargs.pop('entry_date', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        entry = super().save(commit=False)
        
        # Set the user and date
        if self.user and not entry.user_id:
            entry.user = self.user
        
        if self.entry_date:
            entry.entry_date = self.entry_date
        
        if commit:
            entry.save()
        
        return entry


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories"""
    
    class Meta:
        model = Category
        fields = ['name', 'color', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name (e.g., Work, Health, Personal)',
                'maxlength': 100
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional: describe what this category is for...',
                'rows': 3
            })
        }
        help_texts = {
            'name': 'Choose a clear, descriptive name for your category',
            'color': 'Pick a color to help you visually identify this category',
            'description': 'Optional: add more details about when to use this category'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make description optional
        self.fields['description'].required = False

    def clean_name(self):
        name = self.cleaned_data.get('name')
        
        if name:
            name = name.strip()
            
            # Check for minimum length
            if len(name) < 2:
                raise ValidationError('Category name must be at least 2 characters long.')
            
            # Check for uniqueness within user's categories (case-insensitive)
            if self.user:
                existing = Category.objects.filter(
                    user=self.user,
                    name__iexact=name
                )
                
                # If editing, exclude current instance
                if self.instance and self.instance.pk:
                    existing = existing.exclude(pk=self.instance.pk)
                
                if existing.exists():
                    raise ValidationError('You already have a category with this name.')
        
        return name

    def save(self, commit=True):
        category = super().save(commit=False)
        
        if self.user and not category.user_id:
            category.user = self.user
        
        if commit:
            category.save()
        
        return category