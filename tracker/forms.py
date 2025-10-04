from django import forms
from django.core.exceptions import ValidationError
from .models import Entry, Category


class EntryForm(forms.ModelForm):
    """
    The main form for adding/editing daily entries.
    Made to be as user-friendly as possible with good placeholders and styling.
    """
    
    class Meta:
        model = Entry
        fields = ['entry_date', 'title', 'content', 'mood_rating', 'gratitude_text', 'categories']
        
        # Bootstrap classes and helpful placeholder text
        widgets = {
            'entry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'  # Gets the nice date picker
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What was the highlight of your day? (e.g., "Finished presentation", "Had quality time with family")',
                'maxlength': 200
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'List your wins (one per line):\nCompleted project milestone\nHad a great conversation with a friend\nLearned something new\nMade healthy choices\nHelped someone out',
                'rows': 6
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
            'title': '',  # Remove redundant help text - we have clear label and placeholder
            'content': '',  # Remove redundant help text - we have the tip in the template
            'mood_rating': 'How was your overall mood today?',
            'gratitude_text': 'What are you grateful for today?',
            'categories': ''  # Remove redundant help text - label is clear enough
        }

    def __init__(self, *args, **kwargs):
        """
        Setup the form - mainly for filtering categories to only show your own ones.
        Also sets today's date automatically for new entries.
        """
        # Get the user from the view so we can filter categories
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show categories that belong to this user
        if self.user:
            self.fields['categories'].queryset = Category.objects.filter(user=self.user)
        else:
            # No user = no categories (shouldn't happen normally)
            self.fields['categories'].queryset = Category.objects.none()
        
        # Categories are optional - don't want to force people to use them
        self.fields['categories'].required = False
        
        # Auto-fill today's date for new entries
        if not self.instance.pk:  # New entry
            from datetime import date
            self.fields['entry_date'].initial = date.today()

    def clean(self):
        """
        Validation - make sure at least something is filled in.
        Trying to be reasonable and not too strict here.
        """
        cleaned_data = super().clean()
        mood_rating = cleaned_data.get('mood_rating')
        title = cleaned_data.get('title')
        content = cleaned_data.get('content')
        gratitude_text = cleaned_data.get('gratitude_text')
        
        # Check if everything is actually empty
        title_empty = not title or not title.strip()
        content_empty = not content or not content.strip()
        gratitude_empty = not gratitude_text or not gratitude_text.strip()
        mood_empty = not mood_rating
        
        # Ensure at least some meaningful content is provided
        if title_empty and content_empty and gratitude_empty and mood_empty:
            raise ValidationError(
                "🤔 Your entry seems to be empty! Please add at least one of the following: "
                "a title, your wins/achievements, a gratitude note, or select your mood."
            )
        
        # Validate meaningful content length (only if something was entered)
        if title and len(title.strip()) < 3:
            raise ValidationError({
                'title': 'Title should be at least 3 characters long.'
            })
        
        if content and len(content.strip()) < 5:
            raise ValidationError({
                'content': 'Please write at least 5 characters about your wins.'
            })
        
        if gratitude_text and len(gratitude_text.strip()) < 5:
            raise ValidationError({
                'gratitude_text': 'Please write at least 5 characters about what you\'re grateful for.'
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