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
    """Categories for organizing entries - user-specific."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    color = models.CharField(
        max_length=7, 
        default='#007bff',
        validators=[
            RegexValidator(
                regex='^#[0-9A-Fa-f]{6}$',
                message='Color must be a valid hex code (e.g., #007bff)'
            )
        ]
    )
    description = models.TextField(blank=True)
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
    """Model for storing both wins and gratitude entries."""
    
    class EntryType(models.TextChoices):
        WIN = 'win', 'Daily Win'
        GRATITUDE = 'gratitude', 'Gratitude Entry'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    entry_type = models.CharField(
        max_length=10, 
        choices=EntryType.choices,
        db_index=True  # Add index for frequent filtering
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    mood_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True,
        help_text="Rate your mood from 1-10 (optional)"
    )
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    is_private = models.BooleanField(default=True)
    
    # Many-to-many relationship with categories
    categories = models.ManyToManyField(
        Category, 
        blank=True, 
        related_name='entries',
        help_text="Optional categories for this entry"
    )
    
    class Meta:
        verbose_name_plural = "Entries"
        ordering = ['-date_created']
        constraints = [
            models.CheckConstraint(
                name='mood_rating_null_or_between_1_10',
                check=(
                    models.Q(mood_rating__isnull=True) |
                    (models.Q(mood_rating__gte=1) & models.Q(mood_rating__lte=10))
                ),
                violation_error_message='Mood rating must be between 1 and 10 (or left blank).',
            )
        ]
        indexes = [
            models.Index(fields=['user', '-date_created']),
            models.Index(fields=['mood_rating']),
            # Removed separate entry_type index since db_index=True creates one
        ]
    
    def __str__(self):
        return f"{self.get_entry_type_display()}: {self.title[:50]}"


# Signal to prevent cross-user category assignments
@receiver(m2m_changed, sender=Entry.categories.through)
def ensure_same_user_for_categories(sender, instance, action, reverse, model, pk_set, **kwargs):
    """Ensure users can only assign their own categories to their entries."""
    if action in {'pre_add', 'pre_set'} and pk_set:
        # When adding categories to an Entry, ensure they belong to the same user
        categories = Category.objects.filter(pk__in=pk_set).values_list('user_id', flat=True).distinct()
        if categories.count() > 1 or (categories and categories.first() != instance.user_id):
            raise ValidationError("You can only assign your own categories to your entries.")
