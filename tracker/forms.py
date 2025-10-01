from django import forms
from django.core.exceptions import ValidationError
from .models import Entry, Category


class EntryForm(forms.ModelForm):
    """Form for creating and editing wins and gratitude entries"""
    
    class Meta:
        model = Entry
        fields = ['entry_type', 'title', 'content', 'mood_rating', 'categories']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Give your entry a title...',
                'maxlength': 200
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write about your win or what you\'re grateful for...',
                'rows': 6
            }),
            'entry_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'mood_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': 'Rate 1-10 (optional)'
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'title': 'A brief, descriptive title for your entry',
            'content': 'Share the details - what happened, how you feel, why you\'re grateful',
            'mood_rating': 'How are you feeling right now? (1=Low, 10=Amazing)',
            'categories': 'Optional: tag this entry with categories to organize it'
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
        
        # Make categories field optional and improve display
        self.fields['categories'].required = False
        
        # Add dynamic classes based on entry type (can be enhanced with JS)
        if self.instance and self.instance.pk:
            if self.instance.entry_type == Entry.EntryType.WIN:
                self.fields['title'].widget.attrs['placeholder'] = 'What did you accomplish today?'
                self.fields['content'].widget.attrs['placeholder'] = 'Describe your win - what you did, how it felt, why it matters...'
            else:
                self.fields['title'].widget.attrs['placeholder'] = 'What are you grateful for?'
                self.fields['content'].widget.attrs['placeholder'] = 'Express your gratitude - what happened, who helped, why it means something...'

    def clean(self):
        cleaned_data = super().clean()
        entry_type = cleaned_data.get('entry_type')
        title = cleaned_data.get('title')
        content = cleaned_data.get('content')
        mood_rating = cleaned_data.get('mood_rating')
        
        # Validate mood rating range (additional validation beyond model)
        if mood_rating is not None and (mood_rating < 1 or mood_rating > 10):
            raise ValidationError({
                'mood_rating': 'Mood rating must be between 1 and 10.'
            })
        
        # Ensure title and content are meaningful
        if title and len(title.strip()) < 3:
            raise ValidationError({
                'title': 'Title must be at least 3 characters long.'
            })
        
        if content and len(content.strip()) < 10:
            raise ValidationError({
                'content': 'Please write at least 10 characters to make your entry meaningful.'
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
    """Simplified form for quick entry creation from dashboard"""
    
    class Meta:
        model = Entry
        fields = ['entry_type', 'title', 'content']
        widgets = {
            'entry_type': forms.HiddenInput(),  # Will be set by the view
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quick title...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What happened?'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.entry_type = kwargs.pop('entry_type', None)
        super().__init__(*args, **kwargs)
        
        # Pre-set entry type if provided
        if self.entry_type:
            self.fields['entry_type'].initial = self.entry_type
            
            # Customize placeholders based on entry type
            if self.entry_type == Entry.EntryType.WIN:
                self.fields['title'].widget.attrs['placeholder'] = 'What did you win at today?'
                self.fields['content'].widget.attrs['placeholder'] = 'Quick note about your accomplishment...'
            else:
                self.fields['title'].widget.attrs['placeholder'] = 'What are you grateful for?'
                self.fields['content'].widget.attrs['placeholder'] = 'Quick note about your gratitude...'

    def save(self, commit=True):
        entry = super().save(commit=False)
        
        if self.user:
            entry.user = self.user
        
        if self.entry_type:
            entry.entry_type = self.entry_type
        
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