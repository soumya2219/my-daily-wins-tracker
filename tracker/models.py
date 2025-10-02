from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db.models import UniqueConstraint, Index
from django.db.models.functions import Lower
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError

User = get_user_model()


class Category(models.Model):
    """
    Categories for organizing entries - Work, Health, Personal etc.
    User-specific so no cross-contamination between users.
    """
    
    # User ownership
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    
    # Hex color for UI display
    color = models.CharField(
        max_length=7, 
        default='#007bff',  # Bootstrap blue
        validators=[
            RegexValidator(
                regex='^#[0-9A-Fa-f]{6}$',
                message='Color must be a valid hex code (e.g., #007bff)'
            )
        ]
    )
    description = models.TextField(blank=True)  # Optional notes
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        constraints = [
            UniqueConstraint(
                Lower('name'), 'user',
                name='unique_category_name_per_user',
                violation_error_message='You already have a category with this name (case-insensitive).'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'name']),
            Index(Lower('name'), name='idx_category_lower_name'),  # Functional index for case-insensitive lookups
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Entry(models.Model):
    """
    Main daily entry model. One entry per day per user.
    Tracks wins, mood, and gratitude.
    """
    
    class MoodChoice(models.IntegerChoices):
        """1-10 mood scale with emoji labels"""
        TERRIBLE = 1, '😰 Terrible'
        BAD = 2, '😞 Bad'
        MEH = 3, '😐 Meh'
        OKAY = 4, '🙂 Okay'
        GOOD = 5, '😊 Good'
        GREAT = 6, '😄 Great'
        AMAZING = 7, '🤩 Amazing'
        FANTASTIC = 8, '🥳 Fantastic'
        INCREDIBLE = 9, '✨ Incredible'
        PERFECT = 10, '🌟 Perfect'
    
    # User relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    
    # Date - enforces one entry per day
    entry_date = models.DateField(help_text="The date this entry is for", null=True, blank=True)
    
    # Content fields - all optional to reduce friction
    title = models.CharField(max_length=200, blank=True, help_text="Short title for your daily win")
    content = models.TextField(blank=True, help_text="Details about your daily wins")
    
    # Mood tracking
    mood_rating = models.IntegerField(
        choices=MoodChoice.choices,
        null=True,
        blank=True,
        help_text="How was your mood today?"
    )
    
    # Gratitude section - good for mental health
    gratitude_text = models.TextField(
        blank=True,
        help_text="Today I was grateful for..."
    )
    
    # Auto timestamps
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    
    # All private for now
    is_private = models.BooleanField(default=True)
    
    # Categories - many-to-many relationship
    categories = models.ManyToManyField(
        Category, 
        blank=True, 
        related_name='entries',
        help_text="Optional categories for this entry"
    )
    
    class Meta:
        verbose_name_plural = "Entries"
        # Show newest entries first
        ordering = ['-entry_date', '-date_created']
        constraints = [
            # Business rule: one entry per user per day to maintain daily habit
            UniqueConstraint(
                fields=['user', 'entry_date'],
                name='unique_entry_per_user_per_day',
                violation_error_message='You can only have one entry per day.'
            ),
            models.CheckConstraint(
                name='mood_rating_valid_choice',
                check=models.Q(mood_rating__isnull=True) | models.Q(mood_rating__in=[1,2,3,4,5,6,7,8,9,10]),
                violation_error_message='Mood rating must be between 1 and 10.',
            )
        ]
        # DB indexes for performance
        indexes = [
            models.Index(fields=['user', '-entry_date']),  # Dashboard queries
            models.Index(fields=['user', 'entry_date']),   # Day lookups
            models.Index(fields=['mood_rating']),          # Filtering
        ]
    
    def __str__(self):
        """Admin display"""
        return f"{self.user.username} - {self.entry_date}: {self.title[:30] if self.title else 'No title'}"
    
    @property
    def mood_emoji(self):
        """Get emoji for UI display"""
        if self.mood_rating:
            return dict(self.MoodChoice.choices)[self.mood_rating]
        return "😶 No mood set"
    
    @property
    def has_content(self):
        """Check if entry has any content for calendar display"""
        return bool(self.title or self.content or self.gratitude_text or self.mood_rating)


# Security: prevent users from assigning other users' categories
@receiver(m2m_changed, sender=Entry.categories.through)
def ensure_same_user_for_categories(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Data integrity check - make sure users can only assign their own categories.
    """
    if action in {'pre_add', 'pre_set'} and pk_set:
        # Verify all categories belong to entry owner
        categories = Category.objects.filter(pk__in=pk_set).values_list('user_id', flat=True).distinct()
        if categories.count() > 1 or (categories and categories.first() != instance.user_id):
            raise ValidationError("You can only assign your own categories to your entries.")
