from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tracker.views import create_default_categories

User = get_user_model()


class Command(BaseCommand):
    help = 'Add default categories for existing users who don\'t have any categories yet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Add default categories for a specific user (optional)',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        
        if username:
            # Add categories for specific user
            try:
                user = User.objects.get(username=username)
                if user.categories.exists():
                    self.stdout.write(
                        self.style.WARNING(f'User {username} already has categories. No action taken.')
                    )
                else:
                    created_categories = create_default_categories(user)
                    self.stdout.write(
                        self.style.SUCCESS(f'Added {len(created_categories)} default categories for {username}')
                    )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {username} not found.')
                )
        else:
            # Add categories for all users without any categories
            users_without_categories = User.objects.filter(categories__isnull=True).distinct()
            
            if not users_without_categories.exists():
                self.stdout.write(
                    self.style.WARNING('All users already have categories. No action taken.')
                )
                return
                
            total_updated = 0
            for user in users_without_categories:
                created_categories = create_default_categories(user)
                total_updated += 1
                self.stdout.write(f'Added {len(created_categories)} categories for {user.username}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {total_updated} users with default categories.')
            )