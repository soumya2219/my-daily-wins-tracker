from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .validators import validate_username


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user creation form with enhanced validation.
    """
    
    class Meta:
        model = User
        fields = ("username", "password1", "password2")
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Update help text
        self.fields['username'].help_text = 'Letters, numbers and underscores only. 3-30 characters.'
        self.fields['password1'].help_text = 'At least 8 characters with letters and numbers.'
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            validate_username(username)
        return username